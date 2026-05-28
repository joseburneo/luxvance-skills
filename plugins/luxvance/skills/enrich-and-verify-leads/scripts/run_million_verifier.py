#!/usr/bin/env python3
"""Run Million Verifier on a list of emails and update the Luxvance master.

Migrated 2026-05-28: destination is now `core.contacts` in Agency OS, called
via the `upsert_master_contacts` RPC. See bulk_upsert_to_supabase.py for the
contract.

Usage:
    MILLIONVERIFIER_API_KEY=... \
    SUPABASE_SERVICE_KEY=... \
    SUPABASE_URL=https://sgaeggmkmipcoikzqwpy.supabase.co \
        python3 run_million_verifier.py /path/to/emails.json [--workers 20]

Input JSON is a flat array of email strings: ["a@b.com", "c@d.com", ...]
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error, time, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone

p = argparse.ArgumentParser()
p.add_argument("emails_json", help="Path to JSON array of emails")
p.add_argument("--workers", type=int, default=20, help="Concurrent workers (default 20, max 20)")
p.add_argument("--no-upsert", action="store_true", help="Skip writing results back to DB")
args = p.parse_args()

MV_KEY = os.environ.get("MILLIONVERIFIER_API_KEY")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
if not MV_KEY:
    sys.exit("ERROR: set MILLIONVERIFIER_API_KEY")
if not args.no_upsert and (not SERVICE_KEY or not SUPABASE_URL):
    sys.exit("ERROR: set SUPABASE_URL and SUPABASE_SERVICE_KEY (or pass --no-upsert)")

with open(args.emails_json) as f:
    emails = json.load(f)
print(f"Verifying {len(emails)} emails with Million Verifier (workers={args.workers})...")

WORKERS = min(args.workers, 20)  # >20 risks throttling

def verify(email):
    """⚠️ User-Agent override is REQUIRED — default Python UA gets 403."""
    try:
        url = f"https://api.millionverifier.com/api/v3/?api={MV_KEY}&email={urllib.parse.quote(email)}&timeout=10"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88.1"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
            return {
                "email": email,
                "result": data.get("result"),
                "quality": data.get("quality"),
                "free": data.get("free"),
                "role": data.get("role"),
            }
    except Exception as e:
        return {"email": email, "result": "error", "error": str(e)[:200]}

def to_status(r):
    res = r.get("result")
    if res == "ok": return "deliverable"
    if res == "catch_all": return "catch_all"
    if res == "disposable": return "disposable"
    if res == "invalid": return "bad"
    if res == "unknown": return "unknown"
    return "unknown"  # error → don't trust

start = time.time()
results = []
done = 0
with ThreadPoolExecutor(max_workers=WORKERS) as pool:
    futures = [pool.submit(verify, e) for e in emails]
    for fut in as_completed(futures):
        results.append(fut.result())
        done += 1
        if done % 500 == 0 or done == len(emails):
            elapsed = time.time() - start
            print(f"  {done}/{len(emails)} ({elapsed:.0f}s, {done/max(elapsed,1):.0f}/s)")

elapsed = time.time() - start
print(f"\nDone in {elapsed:.1f}s")

# Save raw
out_raw = f"/tmp/mv_results_{int(time.time())}.json"
with open(out_raw, "w") as f:
    json.dump(results, f)

print("\nResult distribution:")
for k, v in Counter(r.get("result") for r in results).most_common():
    print(f"  {k or '(none)':<14} {v:>5} ({v/len(results)*100:.1f}%)")

# Upsert verdicts to DB
if args.no_upsert:
    print(f"\n--no-upsert: skipping DB write. Raw saved to {out_raw}")
    sys.exit(0)

now_iso = datetime.now(timezone.utc).isoformat()
payload = []
for r in results:
    # Skip errors — don't pollute the DB with non-verdicts
    if r.get("result") == "error":
        continue
    payload.append({
        "email": r["email"],
        "email_status": to_status(r),
        "email_verified_at": now_iso,
        "email_verified_by": "million_verifier",
    })

FN_URL = f"{SUPABASE_URL}/rest/v1/rpc/upsert_master_contacts"
total = 0
for i in range(0, len(payload), 2000):
    chunk = payload[i:i+2000]
    req = urllib.request.Request(FN_URL, data=json.dumps({"payload": chunk}).encode(), method="POST", headers={
        "Authorization": f"Bearer {SERVICE_KEY}",
        "apikey": SERVICE_KEY,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = json.loads(resp.read().decode())
        total += res.get("processed", 0)
        print(f"  upsert chunk {i//2000 + 1}: {res.get('processed')}")

errs = sum(1 for r in results if r.get("result") == "error")
print(f"\nUpsert complete: {total}/{len(payload)} verdicts written. Skipped {errs} errors.")
print(f"Raw results: {out_raw}")

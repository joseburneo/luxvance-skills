#!/usr/bin/env python3
"""Run BounceBan on catch_all emails (specialized for catch-all servers).

Usage:
    BOUNCEBAN_API_KEY=... \
    SUPABASE_ANON_KEY_CONTACT_DB=... \
        python3 run_bounceban.py /path/to/catch_all_emails.json [--workers 20]

Run this AFTER Million Verifier, only on the catch_all subset. BounceBan is
specialized and more expensive — don't use it on emails MV could decide on.
"""
import json, os, sys, urllib.request, urllib.parse, urllib.error, time, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone

p = argparse.ArgumentParser()
p.add_argument("emails_json", help="Path to JSON array of catch_all emails")
p.add_argument("--workers", type=int, default=20)
p.add_argument("--no-upsert", action="store_true")
args = p.parse_args()

BB_KEY = os.environ.get("BOUNCEBAN_API_KEY")
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY_CONTACT_DB") or os.environ.get("SUPABASE_ANON_KEY")
if not BB_KEY:
    sys.exit("ERROR: set BOUNCEBAN_API_KEY")
if not args.no_upsert and not ANON_KEY:
    sys.exit("ERROR: set SUPABASE_ANON_KEY_CONTACT_DB (or pass --no-upsert)")

with open(args.emails_json) as f:
    emails = json.load(f)
print(f"Resolving {len(emails)} catch_all emails with BounceBan...")

def verify(email):
    """BounceBan v1/verify/single. Auth: Authorization: Bearer."""
    try:
        url = f"https://api.bounceban.com/v1/verify/single?email={urllib.parse.quote(email)}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {BB_KEY}",
            "User-Agent": "curl/7.88.1",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return {
                "email": email,
                "result": data.get("result"),
                "score": data.get("score"),
                "is_accept_all": data.get("is_accept_all"),
                "is_disposable": data.get("is_disposable"),
                "is_role": data.get("is_role"),
                "smtp_provider": data.get("smtp_provider"),
            }
    except Exception as e:
        return {"email": email, "result": "error", "error": str(e)[:200]}

def to_status(r):
    res = r.get("result")
    if res == "deliverable": return "deliverable"
    if res == "undeliverable": return "bad"
    if res == "risky": return "catch_all"  # still risky after BB
    if res == "unknown": return "unknown"
    return "unknown"

start = time.time()
results = []
done = 0
with ThreadPoolExecutor(max_workers=args.workers) as pool:
    futures = [pool.submit(verify, e) for e in emails]
    for fut in as_completed(futures):
        results.append(fut.result())
        done += 1
        if done % 100 == 0 or done == len(emails):
            print(f"  {done}/{len(emails)} ({time.time()-start:.0f}s)")

print(f"\nDone in {time.time()-start:.1f}s")

out_raw = f"/tmp/bb_results_{int(time.time())}.json"
with open(out_raw, "w") as f:
    json.dump(results, f)

print("\nBounceBan verdict on catch_all:")
for k, v in Counter(r.get("result") for r in results).most_common():
    print(f"  {k or '(none)':<15} {v:>4} ({v/len(results)*100:.1f}%)")

if args.no_upsert:
    print(f"\n--no-upsert: skipping DB write. Raw saved to {out_raw}")
    sys.exit(0)

now_iso = datetime.now(timezone.utc).isoformat()
payload = [{
    "email": r["email"],
    "email_status": to_status(r),
    "email_verified_at": now_iso,
    "email_verified_by": "bounceban",
} for r in results if r.get("result") not in (None, "error")]

FN_URL = "https://nbwbauomozeokflntcwa.supabase.co/functions/v1/bulk-upsert-contacts"
total = 0
for i in range(0, len(payload), 2000):
    chunk = payload[i:i+2000]
    req = urllib.request.Request(FN_URL, data=json.dumps(chunk).encode(), method="POST", headers={
        "Authorization": f"Bearer {ANON_KEY}",
        "apikey": ANON_KEY,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = json.loads(resp.read().decode())
        total += res.get("processed", 0)
        print(f"  upsert chunk {i//2000 + 1}: {res.get('processed')}")

print(f"\nUpsert complete: {total}/{len(payload)}. Raw: {out_raw}")

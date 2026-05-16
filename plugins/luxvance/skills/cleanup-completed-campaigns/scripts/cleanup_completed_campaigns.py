#!/usr/bin/env python3
"""
cleanup_completed_campaigns.py — free Instantly contact quota by removing
no-reply leads from campaigns that are completed, paused, or ≥98% finished
at lead level.

Replied leads (email_reply_count > 0) are always preserved.

Usage:
    python3 scripts/cleanup_completed_campaigns.py --client luxvance
    python3 scripts/cleanup_completed_campaigns.py --client luxvance --execute
    python3 scripts/cleanup_completed_campaigns.py --client kcal --threshold 0.95

Without --execute it prints a dry-run report and exits.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
MASTER_ENV = ROOT / "credentials" / "master.env"
CLI = os.path.expanduser("~/.npm-global/bin/instantly")
API_BASE = "https://api.instantly.ai/api/v2"
LIST_LEADS_URL = f"{API_BASE}/leads/list"
LIST_CAMPAIGNS_URL = f"{API_BASE}/campaigns"

CLIENT_KEY_VARS = {
    "luxvance":          "INSTANTLY_API_KEY_LUXVANCE",
    "kcal":              "INSTANTLY_API_KEY_KCAL",
    "connect-resources": "INSTANTLY_API_KEY_CONNECT_RESOURCE",
    "capquest":          "INSTANTLY_API_KEY_CAPQUEST",
    "gfv":               "INSTANTLY_API_KEY_GLOBAL_FOOD_VENTURES",
    "remly":             "INSTANTLY_API_KEY_REMLY",
}

LEAD_STATUS_COMPLETED = 3
CAMPAIGN_STATUS_PAUSED = 2
CAMPAIGN_STATUS_COMPLETED = 3


def load_api_key(client: str) -> str:
    var = CLIENT_KEY_VARS.get(client)
    if not var:
        sys.exit(f"unknown client '{client}'. known: {sorted(CLIENT_KEY_VARS)}")
    text = MASTER_ENV.read_text()
    m = re.search(rf"^{var}=(.+)$", text, re.MULTILINE)
    if not m:
        sys.exit(f"{var} not found in {MASTER_ENV}")
    return m.group(1).strip().strip('"').strip("'")


def _curl(method: str, url: str, api_key: str, body: Optional[dict] = None, retries: int = 4) -> dict:
    """HTTP request via curl (bypasses Cloudflare's urllib UA block)."""
    args = ["curl", "-sS", "-X", method, url,
            "-H", f"Authorization: Bearer {api_key}",
            "-w", "\n__HTTP__:%{http_code}"]
    if body is not None:
        args += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    last_code = last_body = None
    for attempt in range(retries):
        r = subprocess.run(args, capture_output=True, text=True)
        out = r.stdout
        idx = out.rfind("__HTTP__:")
        last_code = int(out[idx + 9:].strip()) if idx >= 0 else 0
        last_body = out[:idx] if idx >= 0 else out
        if last_code == 200:
            return json.loads(last_body)
        time.sleep(1 + attempt)
    raise RuntimeError(f"{method} {url} failed: HTTP {last_code}: {last_body[:200]}")


def curl_post(url: str, api_key: str, body: dict, retries: int = 4) -> dict:
    return _curl("POST", url, api_key, body, retries)


def curl_get(url: str, api_key: str, retries: int = 4) -> dict:
    return _curl("GET", url, api_key, None, retries)


def list_all_campaigns(api_key: str) -> list:
    items, cursor = [], None
    while True:
        url = f"{LIST_CAMPAIGNS_URL}?limit=100"
        if cursor:
            url += f"&starting_after={cursor}"
        d = curl_get(url, api_key)
        items.extend(d.get("items", []))
        cursor = d.get("next_starting_after")
        if not cursor:
            break
    return items


def sample_completed_ratio(api_key: str, campaign_id: str, sample: int = 100) -> tuple:
    """Return (ratio, sampled) — ratio of leads with lead-status==3 in first page."""
    d = curl_post(LIST_LEADS_URL, api_key, {"campaign": campaign_id, "limit": sample})
    items = d.get("items", [])
    if not items:
        return 0.0, 0
    completed = sum(1 for L in items if L.get("status") == LEAD_STATUS_COMPLETED)
    return completed / len(items), len(items)


def classify(campaign: dict, api_key: str, threshold: float) -> tuple:
    status = campaign.get("status")
    if status == CAMPAIGN_STATUS_COMPLETED:
        return True, "completed"
    if status == CAMPAIGN_STATUS_PAUSED:
        return True, "paused"
    ratio, sampled = sample_completed_ratio(api_key, campaign["id"])
    if sampled == 0:
        return False, f"status={status}, empty"
    if ratio >= threshold:
        return True, f"status={status}, {ratio:.0%} leads completed (sample {sampled})"
    return False, f"status={status}, only {ratio:.0%} completed"


def count_full_campaign(api_key: str, campaign_id: str) -> tuple:
    """Walk every page; return (total, no_reply)."""
    total = no_reply = 0
    cursor = None
    while True:
        body = {"campaign": campaign_id, "limit": 100}
        if cursor:
            body["starting_after"] = cursor
        d = curl_post(LIST_LEADS_URL, api_key, body)
        items = d.get("items", [])
        for L in items:
            total += 1
            if (L.get("email_reply_count") or 0) == 0:
                no_reply += 1
        cursor = d.get("next_starting_after")
        if not cursor:
            break
    return total, no_reply


def fetch_no_reply_ids(api_key: str, campaign_id: str, want: int) -> list:
    """Walk pages until we have `want` no-reply IDs (or run out)."""
    out, cursor = [], None
    while len(out) < want:
        body = {"campaign": campaign_id, "limit": 100}
        if cursor:
            body["starting_after"] = cursor
        d = curl_post(LIST_LEADS_URL, api_key, body)
        items = d.get("items", [])
        for L in items:
            if (L.get("email_reply_count") or 0) == 0:
                out.append(L["id"])
                if len(out) >= want:
                    return out
        cursor = d.get("next_starting_after")
        if not cursor:
            break
    return out


def bulk_delete(api_key: str, campaign_id: str, ids: list, limit: int) -> int:
    """Delete via the CLI. Returns the count actually deleted (per API)."""
    env = {**os.environ, "INSTANTLY_API_KEY": api_key}
    r = subprocess.run(
        [CLI, "leads", "bulk-delete",
         "--campaign-id", campaign_id,
         "--ids", ",".join(ids),
         "--limit", str(limit)],
        capture_output=True, text=True, env=env,
    )
    if r.returncode != 0:
        print(f"  delete error: {r.stderr[:200]}", flush=True)
        return 0
    try:
        return json.loads(r.stdout).get("count", 0)
    except Exception:
        return 0


def execute_campaign(api_key: str, campaign: dict, batch_size: int) -> int:
    """Iteratively list+delete no-reply leads in a campaign. Adaptive batch."""
    cid = campaign["id"]
    deleted = cycles = 0
    effective = batch_size
    while True:
        ids = fetch_no_reply_ids(api_key, cid, want=effective)
        if not ids:
            break
        count = bulk_delete(api_key, cid, ids, limit=batch_size)
        cycles += 1
        deleted += count
        if count == 0:
            print(f"  zero deleted cycle {cycles}, stopping", flush=True)
            break
        if count < len(ids) and count < effective:
            print(f"  cap detected: server processed {count}/{len(ids)} — adapting", flush=True)
            effective = count
        if cycles % 5 == 0:
            print(f"  cycle {cycles}, deleted {deleted}", flush=True)
        time.sleep(0.2)
    return deleted


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", required=True, choices=sorted(CLIENT_KEY_VARS))
    ap.add_argument("--threshold", type=float, default=0.98,
                    help="lead-completion ratio to mark active/draft campaigns eligible (default 0.98)")
    ap.add_argument("--batch-size", type=int, default=1000,
                    help="initial --limit value per bulk-delete call (default 1000, adapts down if server caps lower)")
    ap.add_argument("--execute", action="store_true",
                    help="actually delete (default = dry-run)")
    args = ap.parse_args()

    api_key = load_api_key(args.client)
    print(f"Client: {args.client}   mode: {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print(f"Threshold: {args.threshold:.0%} lead completion for non-paused/non-completed campaigns")
    print()

    print("Listing campaigns...")
    campaigns = list_all_campaigns(api_key)
    print(f"Found {len(campaigns)} campaigns. Classifying...\n")

    eligible = []
    for c in campaigns:
        ok, reason = classify(c, api_key, args.threshold)
        mark = "✓" if ok else "·"
        print(f"  {mark} {c['name'][:60]:<60} → {reason}")
        if ok:
            eligible.append(c)
    print()

    if not eligible:
        print("No eligible campaigns. Nothing to do.")
        return

    print(f"{len(eligible)} eligible. Processing...\n")
    grand_deleted = grand_kept = 0
    for c in eligible:
        name = c["name"][:50]
        if args.execute:
            print(f"{name}: deleting...", flush=True)
            n = execute_campaign(api_key, c, args.batch_size)
            grand_deleted += n
            print(f"  -> {name}: {n} deleted", flush=True)
        else:
            total, no_reply = count_full_campaign(api_key, c["id"])
            replied = total - no_reply
            grand_deleted += no_reply
            grand_kept += replied
            print(f"{name:<50} total={total:>5}  delete={no_reply:>5}  keep={replied:>4}", flush=True)

    print("\n" + "=" * 60)
    if args.execute:
        print(f"TOTAL DELETED: {grand_deleted}")
    else:
        print(f"DRY-RUN: would delete {grand_deleted}, keep {grand_kept} repliers")
        print("Re-run with --execute to actually delete.")


if __name__ == "__main__":
    main()

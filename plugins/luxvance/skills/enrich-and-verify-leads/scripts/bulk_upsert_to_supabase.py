#!/usr/bin/env python3
"""Bulk-UPSERT a CSV of leads into the Luxvance master (Agency OS core.contacts).

Migrated 2026-05-28 from the old Contact DB project (`nbwbauomozeokflntcwa`).
The destination is now `core.contacts` inside Agency OS, called via the
`public.upsert_master_contacts(jsonb)` RPC. Same payload shape, same response
contract {processed, errors}. The RPC handles the schema transformation
(industry → primary_industry, linkedin_url → linkedin_profile, etc.) and the
verified_by mapping (apollo/manual → NULL).

Usage:
    SUPABASE_SERVICE_KEY=... \
    SUPABASE_URL=https://sgaeggmkmipcoikzqwpy.supabase.co \
        python3 bulk_upsert_to_supabase.py /path/to/leads.csv
"""
import csv, json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone

SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
if not SERVICE_KEY or not SUPABASE_URL:
    print("ERROR: set SUPABASE_URL and SUPABASE_SERVICE_KEY env vars", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: bulk_upsert_to_supabase.py /path/to/leads.csv", file=sys.stderr)
    sys.exit(1)

CSV_PATH = sys.argv[1]
FN_URL = f"{SUPABASE_URL}/rest/v1/rpc/upsert_master_contacts"

# Column-name flexibility — accept both Apify/Apollo and snake_case
COL_MAP = {
    "email": "email",
    "firstName": "first_name", "first_name": "first_name", "First Name": "first_name",
    "lastName": "last_name", "last_name": "last_name", "Last Name": "last_name",
    "phone": "phone", "Phone": "phone",
    "companyName": "company", "company": "company", "Company": "company",
    "title": "job_title", "job_title": "job_title", "Title": "job_title",
    "companyIndustry": "industry", "industry": "industry", "Industry": "industry",
    "personCity": "city", "city": "city", "City": "city",
    "personCountry": "country", "country": "country", "Country": "country",
    "companyDomain": "website", "website": "website", "Website": "website",
    "linkedinUrl": "linkedin_url", "linkedin_url": "linkedin_url",
}

def parse_csv(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for raw in r:
            row = {}
            for src, dst in COL_MAP.items():
                if src in raw and raw[src]:
                    v = raw[src].strip()
                    if dst == "industry" and "," in v:
                        v = v.split(",")[0].strip()
                    if v:
                        row[dst] = v
            email = row.get("email", "").lower().strip()
            if not email or "@" not in email:
                continue
            row["email"] = email
            row["apollo_status"] = (raw.get("emailStatus") or raw.get("email_status") or "").strip() or None
            rows.append(row)
    return rows

def upsert(rows, chunk_size=2000):
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = []
    for r in rows:
        apollo = r.get("apollo_status")
        is_apollo_verified = apollo in ("deliverable", "verified")
        payload.append({
            "email": r["email"],
            "first_name": r.get("first_name"),
            "last_name": r.get("last_name"),
            "phone": r.get("phone"),
            "company": r.get("company"),
            "job_title": r.get("job_title"),
            "industry": r.get("industry"),
            "city": r.get("city"),
            "country": r.get("country"),
            "website": r.get("website"),
            "linkedin_url": r.get("linkedin_url"),
            "email_status": apollo or "unknown",
            "email_verified_at": now_iso if is_apollo_verified else None,
            "email_verified_by": "apollo" if is_apollo_verified else None,
        })

    total = 0
    for i in range(0, len(payload), chunk_size):
        chunk = payload[i:i+chunk_size]
        req = urllib.request.Request(
            FN_URL,
            data=json.dumps({"payload": chunk}).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {SERVICE_KEY}",
                "apikey": SERVICE_KEY,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                res = json.loads(resp.read().decode())
                total += res.get("processed", 0)
                print(f"  chunk {i//chunk_size + 1}: processed {res.get('processed')} | errors {len(res.get('errors', []))}")
        except urllib.error.HTTPError as e:
            print(f"  chunk {i//chunk_size + 1}: HTTP {e.code} — {e.read().decode()[:200]}")
    return total

def main():
    print(f"Reading {CSV_PATH}...")
    rows = parse_csv(CSV_PATH)
    print(f"Parsed {len(rows)} valid rows")
    if not rows:
        sys.exit(1)
    print("UPSERT to Contact Database master...")
    n = upsert(rows)
    print(f"\nDone. UPSERTed {n}/{len(rows)} leads.")

if __name__ == "__main__":
    main()

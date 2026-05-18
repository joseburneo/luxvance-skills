#!/usr/bin/env python3
"""Bulk-UPSERT a CSV of leads to the Luxvance Contact Database.

Usage:
    SUPABASE_ANON_KEY_CONTACT_DB=eyJ... \
        python3 bulk_upsert_to_supabase.py /path/to/leads.csv

CSV must have an 'email' column. Other recognized columns (any subset):
    firstName, lastName, phone, companyName, title, companyIndustry,
    personCity, personCountry, companyDomain, linkedinUrl, emailStatus

If 'emailStatus' is 'deliverable' or 'verified' (from Apollo), it's saved as-is
but with email_verified_by='apollo' and email_verified_at=now() — meaning the
MillionVerifier waterfall will still re-verify these later if they're stale.
"""
import csv, json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone

ANON_KEY = os.environ.get("SUPABASE_ANON_KEY_CONTACT_DB") or os.environ.get("SUPABASE_ANON_KEY")
if not ANON_KEY:
    print("ERROR: set SUPABASE_ANON_KEY_CONTACT_DB (or SUPABASE_ANON_KEY) env var", file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print("Usage: bulk_upsert_to_supabase.py /path/to/leads.csv", file=sys.stderr)
    sys.exit(1)

CSV_PATH = sys.argv[1]
FN_URL = "https://nbwbauomozeokflntcwa.supabase.co/functions/v1/bulk-upsert-contacts"

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
            data=json.dumps(chunk).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {ANON_KEY}",
                "apikey": ANON_KEY,
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

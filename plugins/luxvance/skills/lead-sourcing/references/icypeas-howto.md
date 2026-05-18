# Icypeas — how to use

Icypeas is an email finder. Input: LinkedIn profile URLs OR name + company pairs. Output: best-guess work emails.

## Credentials

From `credentials/master.env`:

- `ICYPEAS_API_KEY` — primary auth key
- `ICYPEAS_API_SECRET` — request signing secret

Read both with the `with open()` pattern, NOT `grep`:

```python
def read_env(key):
    with open('/Users/joseburneo/Luxvance_OS/credentials/master.env') as f:
        for line in f:
            if line.startswith(f'{key}='):
                return line.split('=', 1)[1].strip()
    return None
```

## Auth

Icypeas uses a signed-request pattern:

1. Build the request body.
2. Compute an HMAC-SHA1 signature: `HMAC(secret, method + path + body)`.
3. Send headers:
   - `Authorization: <API_KEY>:<SIGNATURE>`
   - `Content-Type: application/json`

Check the up-to-date docs at https://icypeas.com/api-docs before running — auth format has changed at least once.

## Endpoints (verify in the live docs)

### Single email search

`POST https://app.icypeas.com/api/email-search`

Body:

```json
{
  "firstname": "Sarah",
  "lastname": "Chen",
  "domainOrCompany": "acme.com"
}
```

Returns `{ "email": "...", "status": "verified" | "pattern_match" | "not_found", "confidence": 0.0-1.0 }`.

### Bulk email search

`POST https://app.icypeas.com/api/bulk-search`

Body: array of single-search payloads. Returns a `bulkId`. Poll a status endpoint to retrieve results when ready.

For large batches, the bulk endpoint is more efficient. For under 200 lookups, the single endpoint via 20 parallel workers is fine.

## Rate limits

Icypeas allows ~200 requests per minute on the standard plan. Burst above that returns 429. Use 20 concurrent workers as the safe ceiling.

## Hit rate expectations

| Input quality | Hit rate |
|---|---|
| LinkedIn URLs (validated) | 70-80% |
| Name + verified company domain | 65-75% |
| Name + company name only | 45-60% |
| Name only (no company) | <20% — do not use |

If hit rate falls below 40% on a clean input, run Prospeo in parallel for comparison.

## Common failures

- **401 / 403:** auth header malformed. Most often the signature is incorrect (wrong method, missing path, etc.). Validate against the docs' code sample.
- **429:** rate limit. Wait 60 seconds, reduce worker count to 10.
- **Empty `email`:** Icypeas could not find or guess an email. Drop the row, log to `email_source: icypeas_not_found`.
- **`status: pattern_match` with low confidence:** keep but flag downstream. The verifier (MillionVerifier in `enrich-and-verify-leads`) will catch the bad guesses.

## Cost

~$0.03 per lookup on the standard plan. Tier-based discount above 10k/month. Check usage via the Icypeas dashboard before running a large batch.

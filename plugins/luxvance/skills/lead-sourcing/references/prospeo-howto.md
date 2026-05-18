# Prospeo — how to use

Prospeo is an alternative email finder. Same input shape as Icypeas: LinkedIn URLs OR name + company pairs.

## Credentials

`PROSPEO_API_KEY` from `credentials/master.env`. If the key is missing, ask Jose to add it (sign up at https://prospeo.io) — this provider is optional, used mainly when Icypeas hits limits or returns low hit rate.

Read with the `with open()` pattern documented in `icypeas-howto.md`.

## Auth

Single API key in a header:

```
X-KEY: <PROSPEO_API_KEY>
Content-Type: application/json
```

No signature, simpler than Icypeas.

## Endpoints (verify in the live docs)

### Email finder

`POST https://api.prospeo.io/email-finder`

Body:

```json
{
  "first_name": "Sarah",
  "last_name": "Chen",
  "company": "acme.com"
}
```

`company` accepts either a domain or a company name. Domain produces higher hit rate.

Returns:

```json
{
  "response": {
    "email": "sarah.chen@acme.com",
    "verification": {
      "result": "deliverable" | "risky" | "undeliverable",
      "score": 0-100
    }
  }
}
```

### LinkedIn email finder

`POST https://api.prospeo.io/linkedin-email-finder`

Body: `{ "url": "https://linkedin.com/in/..." }`

Returns the same shape as `email-finder`. Useful when the input is a LinkedIn URL list without name + company breakdown.

### Bulk endpoint

Prospeo has a CSV-upload bulk endpoint for batches over 500 lookups. Worth using for 1,000+ rows. Otherwise, single-request endpoint via parallel workers is fine.

## Rate limits

Standard plan: ~100 requests per minute. Use 10-15 concurrent workers.

## Hit rate expectations

Similar to Icypeas. Roughly 60-75% on clean input. Worth running both in parallel on the same input list for comparison when accuracy matters.

## Cost

~$0.02 per lookup. Slightly cheaper than Icypeas. Monthly subscription tiers — check dashboard.

## Why use Prospeo over Icypeas

- **Cheaper per lookup.** Slight cost edge.
- **Simpler auth.** No signature step.
- **LinkedIn endpoint is well-supported.** Icypeas's LinkedIn workflow is less documented.

## Why use Icypeas over Prospeo

- **Existing Luxvance credentials.** Already in `master.env`.
- **Sometimes higher hit rate** on European company domains (Icypeas is a French company).

## Recommendation

Run both in parallel on the first batch of any new input list (50 leads is enough). Pick the higher hit rate for the rest. Document the choice in the campaign brief.

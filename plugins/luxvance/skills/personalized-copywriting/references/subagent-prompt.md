# Subagent Prompt Template

The skill spawns Sonnet subagents via the `Agent` tool to do the actual per-lead variable generation. This file contains the exact prompt template each subagent receives.

The template has three sections:

1. **Header** — role + hard rules + few-shot examples (constant across runs).
2. **Campaign block** — V1 prompt + V2 prompt from `build-campaign` (varies per campaign).
3. **Data block** — the leads to process as a JSON array + output instructions (varies per batch).

The skill assembles the three sections at run time. Below is the canonical text for each section.

---

## Section 1: Header (constant)

```
You are a per-lead variable generator for Luxvance, a B2B cold email agency. You read a LinkedIn-derived snapshot of each lead (job title, company name, company description, website, industry) and output two short phrases per lead:

- variable_1: the prospect's ideal BUYER persona (NOT the prospect themselves).
- variable_2: three named brands matching variable_1's size/scale.

You also normalize each lead's company name.

## HARD RULES (non-negotiable)

1. variable_1 must NEVER echo the lead's own role.
   - If the lead is a Sales Director, variable_1 must NOT be "Sales Directors at X".
     Use a DIFFERENT buyer persona for that offer (e.g. CEO, CFO, COO, CIO, CMO,
     CHRO, CRO, General Manager).
   - Test: read the lead's job title. If variable_1 contains the same role family,
     it is WRONG. Pick a different buyer.

2. variable_2 brand size must MATCH variable_1's size descriptor.
   - "mid-market" V1 → mid-market named brands.
   - "enterprise" V1 → enterprise named brands.
   - "growing companies" V1 → growing-stage brands.
   - Test: imagine the lead reading the email. Would the three named brands feel
     credibly comparable to their company's scale? If not, fix V2.

3. Output format:
   - 2 to 8 words.
   - Lowercase (except proper nouns inside the phrase).
   - No trailing punctuation.
   - No em-dashes.
   - No quotes around the phrase.

4. Source data: ONLY the lead's job title, company name, industry, and website.
   No web search. No hallucinated companies. No invented founders.

5. Approved list FIRST:
   - The campaign block below contains an approved list for variable_1 and one for
     variable_2.
   - If a phrase from the approved list fits the lead, use it verbatim.
   - Only invent a new phrase when nothing in the list maps cleanly to the lead.
   - For variable_2 specifically, the brands you pick should be drawn from the
     approved list. Substituting unknown brands is forbidden.

6. Safe fallback for ambiguous cases:
   - If the lead's industry is genuinely unclear from the data, return the
     documented fallback string from the V1 / V2 prompt (e.g. "growth-stage
     businesses" for V1; "leading brands across the UK" for V2).

7. Company name normalization:
   - Strip legal suffixes: LTD, LIMITED, LLC, INC, INC., PLC, CORP, CORP., GMBH,
     SA, S.A., B.V., BV (case-insensitive).
   - Fix ALL CAPS → Title Case: "JAGUAR LAND ROVER" → "Jaguar Land Rover".
   - Preserve intentional lowercase / mixed brands: iPhone, ThinkAnalytics,
     Black&Callow, IFS assyst. (Detect by: uppercase letter mid-word, or "&" with
     no space, or first 3 letters all caps then lowercase.)
   - Strip trailing punctuation, double spaces, and surrounding quotes.
   - Empty / null company → fall back to email domain, capitalized.

## POSITIVE EXAMPLES (Jose's actual patterns)

Lead: Business Director at Gleeson Recruitment (staffing)
  → variable_1: General Managers at growing companies
  → variable_2: Jaguar Land Rover, Rolls-Royce, and John Lewis

Lead: VP Sales EMEA at ThinkAnalytics (media analytics)
  → variable_1: Heads of Revenue at enterprise companies
  → variable_2: Sky, ITV, and Channel 4

Lead: Business Director at IDEX Consulting (insurance)
  → variable_1: Chief People Officers at insurance carriers
  → variable_2: Aviva, AXA UK, and Zurich Insurance Group

Lead: BD Director at IFS assyst (ITSM software)
  → variable_1: CIOs at enterprise companies
  → variable_2: Tesco, Vodafone, and Unilever

Lead: Sales Director at Black&Callow (legal/IPO services)
  → variable_1: CEOs at enterprise companies
  → variable_2: Aviva, HSBC, and Legal & General

## NEGATIVE EXAMPLES (do NOT do this)

Lead: Sales Director → variable_1: "Sales Directors at SaaS companies"
  ❌ WRONG: echoes lead's own role.
  ✅ FIX: variable_1: "CEOs at SaaS companies" or another distinct buyer.

variable_1: "Mid-market SaaS founders" + variable_2: "Salesforce, Microsoft, and Oracle"
  ❌ WRONG: V2 brands are enterprise, V1 is mid-market.
  ✅ FIX: V2: "HubSpot, Pipedrive, and Freshworks" (mid-market named SaaS).

variable_1: "B2B Software"
  ❌ WRONG: capitalized, 2 words but too generic.
  ✅ FIX: "founders at b2b software firms" (lowercase, specific, 5 words).
```

---

## Section 2: Campaign block (varies per campaign)

The skill substitutes the V1 prompt and V2 prompt from the kit (blocks 6 and 7 of `build-campaign`'s output) here verbatim.

```
## CAMPAIGN VARIABLE PROMPTS

### variable_1 prompt
[verbatim block 6 from build-campaign output, including the approved list]

### variable_2 prompt
[verbatim block 7 from build-campaign output, including the approved list]
```

---

## Section 3: Data block (varies per batch)

```
## LEADS TO PROCESS

Process the JSON array below. For each lead, produce one output object matching the schema. Write the full output array to the file path at the bottom of this prompt.

Input leads (JSON):
[
  {
    "email": "...",
    "first_name": "...",
    "last_name": "...",
    "job_title": "...",
    "company": "...",
    "industry": "...",
    "website": "...",
    "linkedin_url": "..."
  },
  ...
]

Output schema per lead (must match exactly):
{
  "email": "...",                  // pass through
  "first_name": "...",             // capitalized, trimmed
  "last_name": "...",              // capitalized, trimmed
  "company_name": "...",           // normalized per rules above
  "company_domain": "...",         // strip protocol, lowercase, no trailing slash
  "title": "...",                  // lowercase pass-through for natural sentence flow
  "linkedin_url": "...",           // pass through
  "variable_1": "...",             // per campaign prompt + hard rules
  "variable_2": "..."              // per campaign prompt + hard rules
}

Write the output as a JSON array to:
  /tmp/enriched_batch_{N}.json

Confirm completion with a one-line summary: "Wrote N leads to /tmp/enriched_batch_{N}.json. Average V1 length: X words. Approved-list hit rate: Y%."
```

---

## Notes on subagent dispatch

- Use `subagent_type: general-purpose` (needs write access).
- Pass the prompt as-is. Do not paraphrase. The hard rules section is load-bearing.
- One subagent per batch of 800-1,000 leads is the right size. Larger batches risk truncation; smaller batches waste parallelism.
- Do not run more than 4 subagents in parallel to stay within Max plan concurrency limits.

## OpenAI fallback variant

When Jose picks OpenAI gpt-4o-mini, the prompt structure is identical but the dispatch differs:

- Run a Python script that hits OpenAI's API directly.
- Read `OPENAI_API_KEY` from `credentials/master.env` using `with open()` (the gitignored env file).
- Set the system prompt to Section 1.
- Set the user prompt to Sections 2 + 3.
- Use `response_format: { "type": "json_object" }` and ask for `{"results": [...]}`.
- Concurrency: 20 workers max. Backoff on 429.

The Python script lives in `scripts/openai_generate.py` (TBD — to be packaged when Jose first picks the OpenAI path).

# Extraction shadow comparison (#65)

Production event/activity workers still call Gemini and remain the sole database
writers. Their live runs best-effort capture at most two successful Gemini calls
each: exact prompt, response JSON Schema, raw response, model settings and token
deltas including retries/thinking. Capture and artifact-upload failures cannot
fail production. Dry runs do not capture. Successful calls may have yielded zero
accepted listings or later failed persistence; raw captures are not proof of
publication or listing correctness.

The separate `Extraction shadow comparison` workflow triggers after the twice-
daily orchestration or a manual civic/activity workflow finishes on trusted main.
It downloads only `gemini-shadow-input-*` artifacts from that upstream run and
replays at most four exact prompts with OpenAI `gpt-4.1-mini`. No page refetching,
Supabase credentials, venue creation, database imports or publishing code is used.
Failures happen in a separate workflow and do not affect production dependencies.
Originals, news and deals are not shadowed.

Limits: four attempts, 60,000 total reported tokens checked between calls, 3,000
output tokens per request, 90-second HTTP timeout, zero retries and no fallback.
One in-flight request can exceed the remaining run budget. No samples means no
OpenAI calls; this includes Gemini billing failures and unchanged cached sources.
Missing OpenAI credentials/credits fail the comparison without changing production.

Inputs expire after seven days; comparison reports after fourteen. These artifacts
contain public source content and model output; do not use this pipeline for private
or user-submitted material. Reports identify the upstream run and captured prompt
hash, and record per-provider usage, raw listing count and missing/added/changed
fields. They do not equate raw records or schema-valid output with correct accepted
listings. Review source evidence and publication/validation reports before calculating
cost per correctly accepted listing. The first two calls per worker are a bounded
sample, not representative production coverage; vary the review sample if needed.

Dollar estimates are null unless these repository variables are configured using
the current prices for the actual recorded models:

- `SHADOW_GEMINI_INPUT_USD_PER_MILLION`
- `SHADOW_GEMINI_OUTPUT_USD_PER_MILLION`
- `SHADOW_OPENAI_INPUT_USD_PER_MILLION`
- `SHADOW_OPENAI_OUTPUT_USD_PER_MILLION`

Estimates assume uncached standard-rate input and are not billing receipts. Gemini
output accounting already includes thinking; do not add it again. Unknown usage
cannot produce a cost estimate. Keep pricing/model settings in the review record;
configured rates may become stale. This does not change Gemini's production default
or activate #69's worker integrations. The tested shared provider module from #69
is included here for the isolated replay only.

Rollback: remove `SHADOW_CAPTURE_DIR` from collector environments and disable the
shadow workflow. No database migration or data cleanup is required. Disable shadow
review after the several-day evidence period; no automatic end date was specified.

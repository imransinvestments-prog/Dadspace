# Extraction shadow comparison (#65)

## Provider comparison arms — 23 October 2026 (#145)

Four arms run **only on a manual reviewed-cohort dispatch**, never on the automatic
shadow after each collection, so they add no daily spend. Gemini stays the production
default; nothing here changes a production provider variable.

| Variant | Provider | Model (repo variable override) | Secret |
|---|---|---|---|
| `gemini-production` | gemini | `gemini-3.6-flash`, thinking from `GEMINI_EXTRACTION_THINKING_LEVEL` as in production | `GEMINI_API_KEY` |
| `claude-haiku` | anthropic | `claude-haiku-5-5` (`SHADOW_ANTHROPIC_MODEL`), adaptive thinking at effort `medium` | `ANTHROPIC_API_KEY` |
| `deepseek` | deepseek | `deepseek-chat` (`SHADOW_DEEPSEEK_MODEL`) | `DEEPSEEK_API_KEY` |
| `openrouter-free` | openrouter | none by default: set `SHADOW_OPENROUTER_MODEL` to a free model id | `OPENROUTER_API_KEY` |

Each key is passed only to its own arm. Optional rate variables
`SHADOW_<PROVIDER>_INPUT_USD_PER_MILLION` and `_OUTPUT_` feed the usage estimate.
Billed cost still comes from each provider's dashboard.

- **Claude** goes through `llm_claude.py`, using the official `anthropic` SDK with its
  own retries off. It uses structured outputs (`output_config.format`, JSON schema);
  unsupported keywords such as `minLength` and `minimum` are dropped from the schema
  sent, and the reply is still validated against the full schema. `max_tokens` is
  rejected as incomplete, and a refusal is rejected. Thinking is billed inside output
  tokens and is recorded as unknown, not zero. 429 and 5xx responses use the bounded
  retries; any other status is fatal.
- **DeepSeek and OpenRouter** share the OpenAI-compatible chat path: `json_object` mode,
  the schema in the prompt, and validation on return. Only OpenRouter model ids may
  contain `/`.
- **Rollback:** delete the arm from the matrix. No production worker reads these settings.

## Diagnostic and evaluation repair — 15 October 2026

Production provider, thinking, publication and source settings are unchanged.
The 15 October scheduled run was dispatched late; this change does not replace
GitHub's scheduler or claim to fix scheduler delivery. Keep missed-start monitoring.

Rejected Gemini/OpenAI outputs now expose only allowlisted finish/status/reason
codes and non-thinking partial-output character counts. No partial content, remote
error text, request IDs or refusal text is stored. Unknown codes become `unknown`.
Existing token metrics retain unknown-thinking flags; unknown is not zero.

Replay interleaves workers (up to four captures). A content rejection is recorded
and the next distinct capture is considered, with no retry/fallback. Billing,
configuration, budget and uncertain transport failures still stop globally. A run
with rejected, skipped or unsupported samples exits unsuccessfully after saving
its report. Coverage reports include captures not selected under the four-call cap.
This is balanced worker sampling, not proof of representative national coverage.

When a production response's non-thinking output exceeds the shadow response cap,
replay marks it `needs-reviewed-chunks` without a paid request. This avoids repeating
the known full-page ClassForKids comparison. It is a conservative preflight, not
a guarantee that other inputs fit. Limits remain four attempts/60,000 tokens per
variant, 3,000 output tokens/call, zero retries, no fallback. Completing another
sample after rejection can use more of the existing four-attempt allowance than
the previous stop-on-first-failure behavior.

### Prepare and score complete smaller samples

`scripts/prepare_shadow_chunks.py capture.json manifest.json NEW_OUTPUT_DIRECTORY`
is offline. Split only at reviewed complete-record boundaries after `CONTENT:`.
The manifest must cover every source character exactly once, including excluded
candidates and trailing text; the tool rejects gaps, overlaps, missing evidence,
unreviewed boundaries and prompts over 14,000 characters. This size is conservative,
not a token guarantee. No files are written until the whole manifest validates.

Manifest shape (offsets refer to the content after `\nCONTENT:\n`, not the prompt):

```json
{
  "prompt_sha256": "SHA256_OF_EXACT_CAPTURED_PROMPT_UTF8",
  "reviewer": "named reviewer",
  "chunks": [{
    "start": 0,
    "end": 123,
    "complete_records": true,
    "all_candidates_reviewed": true,
    "expected": [{
      "id": "stable-candidate-id",
      "evidence": "exact phrase within this source chunk",
      "fields": {"event_url": "https://example.org/session", "start_date": null,
                 "listing_type": "activity", "age_range": "3–5"}
    }],
    "excluded": [{"id": "adult-talk", "evidence": "Adults only", "reason": "adult audience"}]
  }]
}
```

Review dates, schedule/occurrences, age, family evidence, price, venue and URL;
apply `docs/discovery-model.md` to classification. Review every source candidate,
not just Gemini's returned rows, and include baseline defects in the reference.
The attestations require actual review; the tool cannot certify semantic truth.
Prepare both civic and activity cohorts with varied sources, positive listings,
empty cases and edge cases; repeated copies of one source are not independent data.

Commit reviewed prepared inputs under `artefacts/shadow-cohorts/COHORT_NAME`.
From trusted main only, manually dispatch `Extraction shadow comparison` with that
directory as `reviewed_cohort`. This is an explicit paid evaluation within existing
caps; no manual dispatch has been run as part of this implementation. Both variants
use the identical prepared prompts and source-reviewed reference. Each dispatch
selects at most four samples; organize cohorts of at most four or explicitly account
for unselected chunks. `coverage.json` records full preparation, not full replay.

Reports distinguish `source-reviewed` from `unreviewed-production-output`.
`source_score` checks reviewed fields against unique URL/date matches and lists
ambiguous/missing matches, field differences and unmatched output indices. Exact
title/URL comparisons are review aids: do not discard differing URL queries or
merge different venue/session records automatically. Resolve aliases and semantic
differences against source text; accepted count stays null until that review.
Excluded candidates remain in the reference for false-positive review.

Chunk references have no comparable production baseline usage: baseline cost stays
null even when pricing is configured. Reconcile coverage across all chunks and
record reviewed accepted/missing/incorrect counts before calculating cost per
accepted listing. Chunking itself is not evidence of savings or provider parity.

Rollback this increment by reverting the replay/workflow/provider helper changes;
no database changes are involved. Keep Gemini default until reviewed results justify
a separate rollout decision.

## Minimum-thinking comparison

Shadow jobs now run independently for OpenAI and Gemini minimum thinking on the
same captured prompts. Production Gemini settings stay unchanged. GPT-4.1-mini
has no reasoning step or configurable thinking effort, so its existing replay is
already the non-reasoning comparison; do not send an unsupported reasoning setting
or duplicate an identical OpenAI call. See the [OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-4.1-mini).

The Gemini replay preserves the captured model and uses a documented lowest level:
`minimal` for the current Gemini 3.6 Flash, `low` for 3.8 Flash/3.1 Pro; other
explicitly mapped supported models are listed in `LOWEST_THINKING`. Unknown IDs
are marked unsupported and skipped without a request or model substitution.
`minimal` does not guarantee zero thinking. See [Google's settings table](https://ai.google.dev/gemini-api/docs/generate-content/thinking).
Gemini replay uses REST with temperature 0 and the original captured JSON Schema,
including its array root, rather than the OpenAI object-root wrapper. This is not
an exact SDK/transport reproduction of production; evaluate that limitation and
the bounded output cap in comparisons.

Each provider has its own four-attempt/60,000-token budget and no retries. Total
additional shadow work is now at most eight attempts per upstream run, rather than
four. Matrix fail-fast is disabled, so a Gemini billing/response failure cannot
cancel the OpenAI comparison. Neither can affect production. Artifacts include
variant labels and per-sample actual model/thinking settings, with separate pricing
rates selected for each provider. The captured production response remains the
baseline for both, enabling default-versus-minimum Gemini and cross-provider review.

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
runs each comparison variant on at most four exact prompts. No page refetching,
Supabase credentials, venue creation, database imports or publishing code is used.
Failures happen in a separate workflow and do not affect production dependencies.
Originals, news and deals are not shadowed.

Limits per provider: four attempts, 60,000 total reported tokens checked between calls, 3,000
output tokens per request, 90-second HTTP timeout, zero retries and no fallback.
One in-flight request can exceed the remaining run budget. No samples means no
shadow calls; this includes production Gemini billing failures and unchanged cached sources.
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

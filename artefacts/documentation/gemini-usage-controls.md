# Gemini usage reduction (#65), first implementation

This change removes recurring paid news connectivity tests and automatic PR AI reviews, and gives event/activity extraction configurable usage controls. It does not close #65: content reduction, granular cache work and comparative live quality evaluation remain outstanding. Provider switching is tracked separately in #66.

## Existing measured baseline

The recorded eight-source review on 8 October 2026 used 12 API attempts, 106,199 input tokens, 83,078 output tokens (including thinking), and 189,277 total tokens. Six sources returned accepted rows, with 100 accepted rows across two forced passes and 48 distinct identities after repaired key replay. This is a forced review, not representative production billing or a savings estimate. See `activities-feed-repair-2026-10-08.md` and `artefacts/data/activities-venue-extraction-2026-10-08.json`.

The main ingestion scheduler already runs every two days, deals is rules-only, and news already stores rejected scores. Preserve these controls. Originals' separate generation and editorial review are unchanged.

## Configuration

The two collectors share `gemini_usage.make_extractor`; schemas and deterministic cleaning remain in their original workers. No alternate provider adapter is introduced.

| Environment variable | Default | Meaning |
| --- | --- | --- |
| `GEMINI_THINKING_LEVEL` | blank | Preserve model default. For a compatible model, explicitly select `low`, `minimal`, `medium`, or `high`. Unsupported settings fail rather than silently fall back. |
| `GEMINI_RUN_TOKEN_BUDGET` | 0 | Maximum known total tokens before sending another request; includes thinking. |
| `GEMINI_RUN_MAX_ATTEMPTS` | 0 | Maximum actual generate requests, including retries. |
| `GEMINI_MAX_OUTPUT_TOKENS` | 0 | Optional response ceiling; thinking can consume part of this limit. |
| `GEMINI_MAX_RETRIES` | 2 | Module retries after the initial request. SDK automatic retries are disabled. |

Zero budgets/response ceilings mean no added limit. Civic/activity workflows map repository variables `GEMINI_EXTRACTION_THINKING_LEVEL`, `GEMINI_EXTRACTION_TOKEN_BUDGET`, `GEMINI_EXTRACTION_MAX_ATTEMPTS`, and `GEMINI_EXTRACTION_MAX_OUTPUT_TOKENS` to these environment variables. Blank repository variables preserve current model defaults and unlimited budgets until evaluation chooses suitable values.

Budgets are checked between attempts, not during an in-flight response; they are not a hard billing cap. If a token budget is configured, missing usage after an attempted request stops further requests conservatively. Configure an attempt limit as an independent bound when usage metadata is unavailable. Completed responses include malformed/truncated responses in token metrics. A request that fails before returning usage is recorded as unknown usage rather than zero-cost.

Budget exhaustion leaves the current source unmarked so the next run can retry it. Previous successfully saved sources retain their state. Truncated responses and non-list/non-object output are rejected before cleaning or saving. Actual SDK HTTP timeouts replace the thread wrapper that cannot cancel a network request. The legacy timeout helper remains for other callers.

## Tests and live checks

`gemini-usage-checks.yml` runs mocked controls and existing activity regressions without secrets. News PR checks keep the existing mocked locality regressions and build. Scheduled/manual news collection makes no extra connectivity request. A manual news dispatch can explicitly enable `live_smoke_test`; both that test and a manual AI dry run are paid calls.

The split-baseline workflow keeps its read-only backup/preview automatic, but its two forced Gemini baseline jobs run only on manual dispatch. Venue-source review keeps offline regressions automatic and gates its real two-pass extraction and artifact upload to manual dispatch. The initial PR exposed the split-baseline automatic run; the follow-up gating commit cancelled that superseded run. These paid reviews should be run deliberately for quality evaluation rather than on routine code changes.

The initial civic baseline failed with Gemini HTTP 402: prepayment credits depleted (run 38079392838, 10 October 2026). Live comparative evaluation is blocked until billing is resolved. The caller now treats this as fatal without retries or continuing through more sources. No production writes were made by the read-only baseline. Do not interpret the failed run as quality or savings evidence.

Run:

```sh
python -m unittest discover -s tests -p test_gemini_usage.py -v
python -m unittest discover -s tests -p test_activity_ingestion.py -v
python events_worker.py --self-test
python scripts/test_news_locality.py
```

## Rollout and remaining work

1. Merge offline-tested controls with blank variables; this removes extra news test requests without changing extraction thinking/prompt settings.
2. Capture representative per-worker/source production metrics, including tests, retries, unknown usage, accepted rows and cache-hit rates. Measure Originals too.
3. Capture source HTML once and compare default versus low/minimal on the same pages, date, model and schema. Check missing/incorrect listings, dates, schedules, family evidence, URLs, prices and venues; counts alone are insufficient. Existing forced-review records are a baseline, not proof of equivalence.
4. Choose compatible thinking and budget settings from those results. Do not lower response ceilings blindly: a truncated listing response is rejected and can cause paid retries.
5. Implement/evaluate deduplicated listing input, complete structured-data parsing and normalized/versioned per-page cache with refresh rules. Keep source evidence and commit cache state only after persistence succeeds.
6. Evaluate asynchronous Batch separately: it discounts price rather than reducing tokens and has a target 24-hour turnaround. Current evidence does not justify adopting it yet.

Rollback: clear the extraction repository variables to restore default thinking and remove the optional limits. Revert this PR to restore the previous request/retry implementation and news workflow behavior. Do not close #65 until the remaining quality/savings acceptance criteria are met.

References: [Google thinking](https://ai.google.dev/gemini-api/docs/thinking), [SDK](https://googleapis.github.io/python-genai/), [Batch API](https://ai.google.dev/gemini-api/docs/batch-api).
# Follow-up input and cache controls (#65)

Compact HTML listing nodes are removed from the visible-text fallback only after
their text and links have been captured. Surrounding audience restrictions remain.
Navigation, forms and footers are excluded before listing selection; duplicate
JSON-LD objects are collapsed. JSON-LD and visible evidence remain separate where
they may contain different fields. No complete event is inferred deterministically
from incomplete metadata.

The existing `sources.last_hash` stores a versioned digest of normalized evidence,
prompt rules, extractor/schema factory, validation function, model/provider
configuration and output-affecting date/relevance settings. This intentionally
hashes surrounding evidence too: ignoring it could miss changed age restrictions.
`EXTRACTION_CACHE_VERSION` defaults to `2`; bump it when changing helper/schema
behavior that is not captured by the factory/validator fingerprint.
`EXTRACTION_REFRESH_DAYS` defaults to `7`; `0` disables cache skips. Invalid, future
or expired success timestamps trigger processing. `FORCE_REREAD=true` bypasses the
cache in both collector entry points. Successful state is still advanced only by
the existing post-persistence path; dry runs do not change it. `cache_hits` is
included in the run summary. Existing hashes invalidate once on rollout, so the
first run may cost more; use existing attempt/token budgets to spread that work.
Rollback by reverting this change; that likewise causes one cache invalidation.

Offline saved-page comparison on 11 October 2026 against main `772a075`:

| Saved source page | Before chars | After chars | Removed |
| --- | ---: | ---: | ---: |
| Cardiff Hubs events | 13,837 | 9,114 | 4,723 |
| Museum Wales what's on | 33,817 | 32,255 | 1,562 |

These are prepared-character counts from two listing pages (no detail expansion),
not billed tokens, production savings or quality equivalence. Repeat with
`python scripts/measure_extraction_input.py SNAPSHOT_DIR --baseline REF`; JSON
snapshots contain `url` and `documents` (URL/HTML pairs). The tool uses saved input
and makes no network, model or database calls. Include browser pages, detail pages,
news and Originals before claiming representative savings.

Google's [Batch API](https://ai.google.dev/gemini-api/docs/batch-api) offers 50% of
interactive pricing with a target turnaround of up to 24 hours. This reduces cost,
not tokens. Do not enable it for scheduled slot-specific Originals or fresh news
without a durable job/result queue, retry/idempotency handling and freshness checks
at result application. Keep synchronous extraction for now; evaluate Batch on a
bounded historical/backfill job once billing and quality baselines are available.

## Per-page results and complete structured sources

The optional per-page path processes every fetched document independently and
merges results through the existing cleaner. `EXTRACTION_PER_PAGE=true` enables
it for a bounded evaluation; alternatively a reviewed source may supply
`extraction_mode=per_page`. Neither is activated by this PR. The first extraction
may make more calls than the whole-source path; compare warm-cache savings against
that cold-run cost before enabling it. Existing shared attempt/token budgets apply.

Set `EXTRACTION_CACHE_DIR` to a disposable persistent directory. Civic/activity
workflows restore and save `.extraction-cache` using GitHub Actions cache only when
the per-page variable is true. Live runs save committed entries; dry runs never
write entries or save the Actions cache. Entries contain public extracted fields,
not credentials or source HTML. Eviction/corruption is an ordinary cache miss.
Unchanged documents reuse raw results, which pass current validation again. A
changed document calls AI once; all fetched documents are included in the source
digest even beyond the combined input limit. Hits retain their original extraction
date. Expired historical URL entries are pruned on successful cache commit.

New entries stay in memory until both listing persistence and a source-status
update returning that source ID succeed. Budget/fatal failures, malformed page
results, cleaner exceptions, failed/empty status updates, row save failures and
dry runs discard them. Relative-date evidence includes today's date in its digest,
so a cached interpretation of "tomorrow" cannot carry into another day. A page
reaching the input limit fails before its AI request; partial sources do not commit.

`structured_events_complete=true` opts a reviewed source into strict JSON-LD
parsing. Every record must have a visible title/description and family signal,
timezone-aware start/end, venue/address/postcode, GBP price and a linked event URL.
Recurring schedules, incomplete/ambiguous records and ungrounded descriptions
fall back as a whole. Existing date/family/venue validation still applies. No
source is opted in by this change; review metadata coverage first. This flag is
an in-memory/source-configuration capability, not a new database column/migration.

`scripts/review_usage.py` and civic `usage_review_only` provide a four-request
OpenAI before/after comparison on the same saved Cardiff/Museum Wales HTML. The
job pins #69's provider module and uses a 40,000-token run budget with no retries;
production collection is skipped and no database credentials are supplied. It
saves raw/accepted output, token usage, missing/added listings and changed fields.
This validates input preparation with OpenAI; it does not establish Gemini parity
or representative savings across news, Originals and browser/detail sources.

Still outstanding: production representative measurement, full listing coverage
and grounded family-evidence validation (#69), Gemini-specific comparison while
billing is blocked, and source-by-source activation review. #66 selects providers
per worker; neither issue implements dynamic allocation or automatic fallback.

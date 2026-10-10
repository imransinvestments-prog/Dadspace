# Gemini usage reduction (#65), first implementation

This change removes recurring paid news connectivity tests and automatic PR news collection, and gives event/activity extraction configurable usage controls. It does not close #65: content reduction, granular cache work and comparative live quality evaluation remain outstanding. Provider switching is tracked separately in #66.

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

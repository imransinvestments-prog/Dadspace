# LLM providers

`llm_provider.py` supplies structured generation for events/activities, news
scoring/grouping, and Originals generation/editorial review. Credentials stay in
server-side environment variables and GitHub Actions secrets.

## Enable OpenAI

1. Add a funded OpenAI API key as the repository Actions secret `OPENAI_API_KEY`.
2. Run **LLM provider smoke (manual, one request)** using `openai` and
   `gpt-4.1-mini`. It checks a fixed synthetic source and writes only an artifact.
   It does not access Supabase. Before merge, the existing **Collect events
   (councils, heritage & niche venues)** workflow also exposes `llm_smoke_only`
   on this feature branch; that mode skips collection and database access. The model supports Responses and Structured
   Outputs: [official model documentation](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
3. Set repository Actions variables `LLM_PROVIDER=openai` and
   `LLM_MODEL=gpt-4.1-mini`. To migrate only collectors first, set
   `EXTRACTION_LLM_PROVIDER=openai` and `EXTRACTION_LLM_MODEL=gpt-4.1-mini`
   instead. Start with bounded dry runs and inspect the existing review reports.
4. Repeat the saved real-page quality comparison in #65 before increasing
   production throughput. A synthetic smoke check establishes connectivity and
   schema handling, not production extraction quality or cost savings.

An existing scoped override wins over global settings. Clear obsolete scoped
variables when changing all workers. API billing is separate from ChatGPT plans.

## Configuration

| Setting | Behavior |
| --- | --- |
| `LLM_PROVIDER` | `gemini` (default), `openai`, or `deepseek` |
| `LLM_MODEL` | Explicit API model; required for OpenAI/DeepSeek |
| `EXTRACTION_LLM_PROVIDER/MODEL` | Collector override |
| `NEWS_LLM_PROVIDER/MODEL` | News override |
| `ORIGINAL_CONTENT_LLM_PROVIDER/MODEL` | Originals override |
| `GEMINI_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY` | Secret for selected provider only |
| `LLM_RUN_MAX_ATTEMPTS` | Request cap, including transport retries; 0 means uncapped |
| `LLM_RUN_TOKEN_BUDGET` | Stop before next request at this reported token total; 0 means uncapped |
| `LLM_MAX_OUTPUT_TOKENS` | Per-request output cap; default 6000 for alternative adapters |
| `LLM_MAX_RETRIES` | Default 2, maximum 5; REST adapters retry transport failures only |

Generic controls take precedence over their `GEMINI_` equivalents. In-flight
requests can overshoot a token budget; use the output cap and provider billing
limits as well. Missing usage is recorded explicitly and stops further requests
when a token budget is configured. Thinking tokens are included in output once;
providers that do not report them increment `unknown_thinking_attempts`.

With no provider variables, collectors retain the existing Gemini SDK and legacy
model/thinking settings. News retains its configured Gemini thinking level.
Originals retain `ORIGINAL_CONTENT_MODEL` as the Gemini model override.

## Capabilities and failure handling

- OpenAI uses Responses with strict JSON Schema and `store=false`. Array schemas
  are wrapped in an object at the API boundary, then unwrapped locally.
- DeepSeek uses Chat Completions JSON mode plus local JSON Schema validation.
  JSON mode alone does not guarantee a matching schema. Choose a model that
  supports JSON mode; no beta tool-call dependency is needed.
- Gemini extraction keeps its tested SDK behavior. Other Gemini calls use REST
  structured JSON and local schema validation.
- Gemini SDK extraction retains its legacy bounded retry policy, including malformed
  output retries. This compatibility path can be constrained with the request cap.
- There is no automatic fallback. Provider changes are an explicit operator
  action. Malformed output, schema failures, refusals and truncation are rejected
  without additional paid retries in the REST adapters. Authentication/configuration/billing HTTP
  errors stop immediately. Only transient transport errors, 429 and 5xx retry.
- Existing source evidence, dates, location, relevance and publication checks
  remain in the workers. Originals still requires a separate editorial review;
  a rejected/missing review never publishes. Generation and review share a budget.
- `pipeline_runs.gemini_calls` is a historical database field name; its count now
  covers attempts to the selected provider. Logs identify provider and model.
  No database migration is required.

## Rollback and verification

Set `LLM_PROVIDER=gemini` and remove `LLM_MODEL` plus scoped overrides to return
to legacy models. Restore Gemini billing before running paid collectors.

Offline: install `requirements.txt`, run `python -m unittest discover -s tests
-p 'test_*.py'`, `python scripts/test_news_locality.py`, and
`python events_worker.py --self-test`. Mocked adapter tests cover wrapping,
validation, usage, budgets, provider selection, and credential failures.

Live comparisons remain manual and use the same saved pages across providers.
Do not infer equivalence from mocked tests or automatically activate a provider
after a synthetic smoke check.

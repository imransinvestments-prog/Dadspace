# PR #69: completed work and release decisions — 13 October 2026

PR: https://github.com/imransinvestments-prog/Dadspace/pull/69

Engineering improvements and a bounded live comparison are complete. The branch
targets current main and remains a draft pending the release/quality decisions
below. No source, provider configuration or production data was changed.

| Task | Result |
| --- | --- |
| Integrate current main | Done: preserved activity dates/session adapters, Sutton qualification, caching, shadow review and minimum-thinking support; resolved five conflicts. |
| Ground family suitability | Done: an audience label or score cannot substitute for an exact, source-local child/family phrase or explicit child age band. Neighbouring cards/navigation and unsupported paraphrases cannot qualify a model listing. |
| Repair input coverage | Done: detect truncation before paid extraction; reject partial collection. Cardiff has an opt-in, robots-aware, observed-link paginator capped at 20 pages. All 18 observed pages fetched without model/database calls. |
| Compare providers | Done for two saved public pages, not representative acceptance. Cardiff agrees on identities but differs on one category; Museum Wales has a material coverage/field gap. |
| Merge/release | Held for the release decision. The new validation affects Gemini as well as alternative providers; retaining Gemini as default does not make this a behaviour-neutral deployment. |
| Activate alternatives | Held: successful representative runs, human quality review and worker-specific rollout acceptance remain. Gemini stays default. |

## Coverage findings

[Public coverage manifest](../data/pr69-public-coverage-2026-10-13.json): Cardiff's
18 listing pages total 168,919 prepared characters; individual pages range from
8,799 to 10,625. Combine them into one 40,000-character request and useful supply
would be lost. Use per-page extraction with an explicit source/run budget before
activation. This paginator does not certify branch/detail completeness.

Museum Wales's listing is 33,126 prepared characters: it fits 40,000 but exceeded
the former 18,000-character review cap. Whole-source and per-page extraction now
check the uncut preparation rather than silently treating a cut-off page as complete.
Neither source was activated by this work.

## Live comparison

Initial run: https://github.com/imransinvestments-prog/Dadspace/actions/runs/38422443530

Continuation: https://github.com/imransinvestments-prog/Dadspace/actions/runs/38423746573

Both use exactly the same saved source pages across providers. Database credentials
were absent and production collection was skipped. The first run completed Cardiff
but rejected Museum Wales's incomplete Gemini response at a 10,000-output-token
limit. Continuation reused Cardiff results and snapshots, increased the review-only
limit to 32,000 and made only the two unfinished Museum Wales calls. Zero automatic
retries. The shared budget is checked between calls; it cannot interrupt an in-flight
response. Production model limits remain unchanged.

| Source | Gemini raw / accepted | OpenAI raw / accepted | Finding |
| --- | --- | --- | --- |
| Cardiff Libraries, first page | 2 / 2 | 7 / 2 | Same two accepted identities, with one category difference; OpenAI's other five claims fail source-local family grounding. |
| Museum Wales listing | 18 / 15 | 15 / 11 | Four genuine URL/date identities missing from OpenAI; several shared fields differ. |

Final rules were replayed offline against the exact saved HTML and raw responses;
the counts remained unchanged. This is deterministic acceptance, not Imran's human
quality score. [Listing fields, validation and usage](../data/pr69-provider-review-2026-10-13.json).

OpenAI omitted Waterfront Wildings, Festive Fun with Mrs Claus, Mrs Claus Magical
Christmas and Festive Stop Motion Animation workshops. A decorative title change
for Big Waterfront Christmas is recorded separately, rather than counted as
missing/additional supply. Shared rows differ in age guidance, cost, time or
recurrence. Neither provider's result is automatically the ground truth.

Five paid attempts across both runs used 75,417 total tokens, including the rejected
Museum Wales request. Successful paired requests used 31,720 tokens with Gemini and
20,794 with OpenAI. These token totals do not establish billed-dollar savings or
quality equivalence; source facts and provider-specific prices still need review.

## Scheduled evidence

On 13 October, the main civic collector saved/updated 105 records from 55 sources
using 39 Gemini attempts and 396,752 tokens. Activities saved/updated seven records
from seven sources using seven attempts and 56,680 tokens. Source fetch/quality
failures still exist even though those collector jobs succeeded.

Run: https://github.com/imransinvestments-prog/Dadspace/actions/runs/38358192395

Originals failed its word-count validation (123 words) in scheduled run
https://github.com/imransinvestments-prog/Dadspace/actions/runs/38357718013 .
This is not a current Gemini credit failure and not evidence of alternative-provider
editorial acceptance. Deals failed separately; those repairs are outside #69.

The first scheduled OpenAI shadow artifact contains four empty listing results
under both providers: 15,656 baseline tokens and 13,142 shadow tokens. It proves
connectivity only. [Summary](../data/pr69-shadow-evidence-summary-2026-10-13.json).
Shadow capture now keeps the first two nonempty raw outputs per collector, preserving
its existing sample cap and adding no production requests. It is still a convenience
sample, not a representative benchmark. Continued scheduled evidence is necessary.

## Validation and limitations

Local full suite: 221 tests, 207 passed and 14 provider tests skipped because local
LLM dependencies were unavailable. Those tests are executed by Linux provider CI.
Action-console checks and the collector self-test passed. New tests cover local
quotes versus neighbouring/global text, child versus senior age bands, observed
pagination/access/budget failures, pre-request truncation rejection, resume without
repeated paid calls and nonempty shadow sampling.

Linux provider/usage, shadow, deals/full regressions, news, Originals, SEO, civic safety, venue-review and baseline workflows passed on engineering head `c8a4468`. [Provider checks](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38425366390), [shadow checks](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38425366433), [full regressions](https://github.com/imransinvestments-prog/Dadspace/actions/runs/38425366431). MyLibrary's separately
documented Ealing/Merton runner HTTP 403 remains a source-qualification failure,
not a reason to waive regressions or enable those sources.

News/Originals provider integration has mocked tests, but representative live
editorial comparison remains incomplete. DeepSeek is implemented and mock-tested
but has no live qualification. Full 18-page Cardiff AI extraction and reviewed
source activation were not performed. No historical records were withdrawn here.

## Decisions for Imran

1. **Release timing:** merge the engineering fixes with Gemini still default now,
   accepting conservative rejections/incomplete-source failures, or hold release
   until a wider source review measures their impact? Recommend the wider review;
   this two-page pilot does not justify a broad quality claim.
2. **Initial alternative-provider scope:** collectors on individually reviewed
   sources first, or also news/Originals? Recommend collectors first; the Museum
   Wales coverage/field gap must be resolved before activation, and news/Originals
   need their own editorial evidence. Existing instruction to keep Gemini default
   until several days of successful evidence and owner review still applies.
3. **DeepSeek scope, optional:** defer live DeepSeek qualification from the initial
   OpenAI rollout, or include it with a funded model/Actions secret and its own
   bounded quality review? Recommend defer; never paste credentials into a ticket.

No decision to switch a provider is being inferred from passing tests, elapsed time,
the synthetic smoke or lower token counts. #65/#66 and PR #69 remain open.

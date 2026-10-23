# Provider comparison cohort, 23 October 2026 (#145)

**Reviewer:** Claude AI source review. The owner spot-checks about 10 references on
`/ops/reviews/145`. These are source-reviewed references, not human-approved gold labels.

**Size:** 15 samples (8 council-events and 7 activities), with 94 expected records and
40 exclusions. `cohort.json` lists each sample; `review.json` is the spot-check view.

- **Samples 1–4:** the 15 October cohort, carried forward unchanged. They cover the
  ClassForKids omissions and Penguins Palace venues, the holiday camps, Archive Explorers
  and the Cambridgeshire regular index.
- **Samples 5–15:** new. They were rebuilt offline on 23 October with
  `scripts/rebuild_shadow_captures.py`. That script runs the collector's own robots check,
  fetch, page preparation and `build_prompt`, with each worker's production settings
  (civic uses `requests`; activities uses the browser with `MAX_CHARS=24000`). It records
  the prompt instead of calling a model: **no model calls and no database access**. A
  contiguous run of complete records was then selected from each page, keeping the exact
  production instructions. `reference.selection` records the original prompt hash and the
  character span used.

| # | Source | What it tests |
|---|---|---|
| 5 | Camden Council | 16 regular under-5 sessions across 10 libraries, with a venue and postcode for each |
| 6 | Kempton Steam Museum | Ambiguous years, a cancelled month, past dates, a special event with no audience; one expected event |
| 7 | The Broads Authority | Family events next to adult dinners, a pub night, talks, volunteering and fairs |
| 8 | Kent (See Kent family search) | Specific seasonal family events versus round-up pages, a general festival and a placeholder date range |
| 9 | Oxfordshire | Recurrence: one weekly Rhymetime listed as many rows with a bogus 2030 end date; two distinct Didcot sessions |
| 10 | Peterborough | Family-tagged events next to adult comedy, gigs and a mediumship evening |
| 11 | ClassForKids London | Class cards with ages and postcodes, including online-only and wider-age classes |
| 12 | Hoop London | Same-title sessions at different times are distinct; several have no class on 23 Oct (half term) |
| 13 | Hoop Greater Manchester | Deduplication across repeated days; a teen-only class to exclude |
| 14 | ClassForKids Manchester | Venue identity: one provider at three studios is three activities |
| 15 | Ni 4 Kids | News articles mixed into an events list; a general arts festival and an evening concert |

**Scoring rules for these references**

- Only the fields listed for a record are scored. Where the text is ambiguous (a venue,
  or whether a single dated session is regular), the field is left out rather than guessed.
- Classification follows `docs/discovery-model.md`: regular means activity, rare means
  event, judged from regularity evidence rather than from a date or the source category.
- Exclusions marked "ambiguous" are review items. An arm that returns one is not
  automatically wrong.
- Titles, prices and times are compared semantically. A different rendering is not an
  error by itself.

**Limits**

- The selected records are a slice of each page. This cohort does not cover whole pages,
  all collectors or national supply, and it does not establish quality equivalence.
- The 23 Oct pages may change after today. The samples are frozen and are never refetched.
- There is no paid production response for these prompts, so no baseline cost exists. The
  `gemini-production` arm supplies the Gemini baseline.
- Museum Wales is no longer an active source. Its earlier regression stays on record in
  #145 only.

Replay: from trusted main, dispatch *Extraction shadow comparison* with
`reviewed_cohort = artefacts/shadow-cohorts/quality-2026-10-23`. Every arm gets identical
prompts, with no retries and no fallback.

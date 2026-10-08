# Dadspace news locality — release candidate

Status: production release approved by the owner on 8 October 2026, following successful integrated regression checks and production build. See [production launch](production-launch-2026-10-08.md) for the rollout record. The earlier inspection and draft-review notes below are historical.

## User-visible changes

- Using location shows UK-wide news, nation-wide news for the user's nation, and matching English-region, council-district and county-wide stories.
- A district-specific story does not appear throughout its county merely because it carries county context.
- Geography uses coarse council districts rather than ward/parish names. Old saved ward-based preferences are discarded once; users can select location again. Nation selection is retained.
- Existing unclassified news keeps the previous UK/nation behaviour until it expires from the 14-day feed. Selecting All UK, or selecting a nation without location, remains broad.
- The corrected feed view restores one card per story by excluding articles already marked as secondary versions.

## Technical changes

- Fix strict TypeScript errors that reproduced the failed production build at the previous PR head.
- Share geography normalisation and supported-region aliases between the client/API and existing worker adapter, with a pinned ONS May 2026 reference of 361 council districts and 21 administrative counties. No runtime reference lookup or update job is added.
- Validate persisted/API location values before building raw PostgREST filters; reject malformed tokens, old versions, and conflicting saved nation/location pairs.
- Round coordinates in the browser before sending them to the region endpoint; reject missing/blank coordinates; ignore pseudo-counties.
- Extend the existing self-test scoring call with eight representative geographic cases. Missing raw geography now fails the test instead of passing through defaults.
- Print and retain raw/normalised geography, snippets and warnings during dry runs. Malformed, unsupported or unsubstantiated geography remains explicitly unclassified rather than being relabelled nationwide. Only named council/county/region evidence can narrow a story; publisher catchment and unrecognised town names cannot.
- Add PR build/regression checks and a same-repository classification dry run to the existing news workflow. Production schedules are unchanged; forked PRs do not receive worker secrets.
- Prepare the existing news_locality.sql correction, preserving the view's column order, age/relevance rules and public read access. Remove public mutation permissions on the updatable view; the underlying news table stays protected by its existing RLS.

## Scope and limitations

Local matching uses the council district/unitary authority, not a street-level radius or every named village. Official district/county names and their nation are checked against the pinned reference; source geography cannot be inferred solely from a publisher. Articles naming only a town within a larger district remain unclassified unless the council is also named. LLM classification still needs review.

Postcodes.io supplies the supported English regions. Unsupported broad labels such as South Wales remain unclassified and use the nation fallback; they are included in the review warnings. Council-level local stories work across all four UK nations.

No article backfill is performed. No additional worker, scheduler or model call is introduced. Existing self-test and scoring calls receive additional geography instructions/cases, so their token counts may increase. Refresh the pinned reference manually if council boundaries change; its publisher, edition, source and licence are stored in news_geography.json.

## Database release step

The previous PR already exposed the geography columns in production. This correction is staged only. At inspection, the live view showed 184 eligible articles including 43 marked non-primary; its corrected predicate would show 141 cards at that snapshot. These counts change as news ages and arrives. No rows need deleting.

After approval, apply news_locality.sql, confirm the view remains readable by anon/authenticated roles and excludes non-primary rows, then merge the reviewed PR. Do not switch the view to security_invoker without first designing table policies: the current news_items table has RLS and no public read policy, so that would hide all news.

## Validation and approval checklist

The final validation results and commit identifiers are recorded in the PR description and the approval release note supplied with this change.

Before release require: production build success; passing locality regression checks; successful Vercel preview; reviewed raw/normalised classification artifact; confirmation of the SQL correction and public-view access.

## Rollback

Revert the application/workflow commit to return to the preceding app behaviour. Keep the additive geography columns. Keep primary-story filtering and public read-only view permissions: they correct existing behaviour independently of personalisation. If new classification needs pausing, point the existing news workflow back at news_worker.py; new rows will remain unclassified and use the nation fallback.

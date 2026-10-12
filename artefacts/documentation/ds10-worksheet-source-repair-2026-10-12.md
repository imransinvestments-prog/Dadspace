# Worksheet source repair — 12 October 2026

## Completed

[Fresh public-page audit](../data/ds10-worksheet-date-audit-2026-10-12.json): all 100 frozen worksheet rows accounted for, 88 distinct HTTPS detail URLs, 82 readable responses, five fetch failures and one cross-host redirect requiring review. HTTP readability and schedule signals are not accepted/current supply. Five worksheet rows lack a usable detail link. Audit and previews make no database writes/model calls.

Expanded opt-in `published_activity_dates` detail enrichment to HAY Cambridge/South Cambs, Hoop and Redbridge alongside Oxfordshire/Coventry. HAY preserves complete published clock/recurrence/exception wording and does not manufacture monthly dates. Hoop requires matching title/URL/structured session, regularity and consistent displayed clocks; descriptions with extra clock times require manual session association. Redbridge preserves the named programme's single date, clock and available recurrence wording. Missing/ambiguous/multi-venue schedules and oversized date lists fail rather than inventing dates or silently truncating useful evidence. Registry routes are not automatically activated.

Added opt-in `classforkids_calendar`: public rendered timetables supply observed booking IDs, then public detail pages supply actual class names, ages, weekday/time, exact remaining dates, venue/postcode and price for remaining sessions. Provider-only root names are not classes. Missing shells, over-budget directories, foreign booking URLs, cancelled/full classes and incomplete/expired published session lists fail. No guessed IDs, private APIs or inferred dates. Limits: eight observed classes per reviewed source; source narrowing required for larger directories. Rendering can still fail and is not certified merely by an HTTP 200.

Browser verified Little Movers' five autumn classes and the Mini Movers detail. [Normal-worker two-pass detail evidence](../data/ds10-classforkids-live-2026-10-12.json) retains ten exact remaining Wednesdays, 14 October–16 December, age 18 months–3 years, Grace Point N1 2SN and £150 for remaining sessions. Actual robots checks pass, identities repeat, model calls/database writes are zero. This is one observed class-detail route, not complete ClassForKids platform coverage or pilot coverage.

[Backfill preview](../data/ds10-date-backfill-preview-2026-10-12.json): 20 rows across 19 URLs have recovered date/schedule fields; 19 require schedule/ambiguity review, 56 require further operator-route work, five lack details. This preview is not a quality score and includes duplicated stored titles/IDs separately. Existing records are unchanged. Re-fetch the page, verify current record identity/provenance, review changed classification and check concurrent updates before any approved backfill.

All 122 Python tests pass locally. Added two-pass read-only CI route checks for Saturdads, Hoop Little Forts and ClassForKids Mini Movers. CI host access must be checked independently; local success does not establish unattended supply.

## Outstanding engineering tasks

- ClassForKids: inspect remaining reviewed clubs' rendered schedules and observed class details, qualify bounded narrower source routes, replace provider-only listings through a reviewed reconciliation process. Preserve per-class/venue ages and price basis.
- HAY: follow published operator/booking links for incomplete clocks; split multi-venue Stay and Play schedules into evidenced individual opportunities. Do not guess clocks for GK Fit, Shake/Rattle/Roll, Mini Athletics, Sing and Sign, Wildlings or HonC.
- Hoop: resolve title aliases against source identities, clock/description contradictions and unqualified regularity; keep conflicts out of automatic backfill.
- Hertfordshire/Library Live: collect named branch schedules from the published catalogue/locator rather than dated blog headers or promotional summaries.
- Southwark/Explore Essex: investigate long calendar occurrence lists against term-time wording and zero/contradictory clock ranges; dated ranges alone do not establish active daily/weekly sessions.
- NCT: retain published exact occurrence dates and independently review regular programme vs first-aid course/nearly-new-sale classification. Do not bulk treat dated sessions as Events.
- Salford and failed NCT detail: investigate the returned fetch failures/expired routes; capture successful runner evidence before refresh/activation.
- Redirected/missing detail links: follow only verified provider links and retain evidence, instead of invented URL variants.
- Historical rows: execute a reviewed merge/reclassification/withdrawal process with pre-write backup and concurrent-row checks; no blanket deletion or automatic verification refresh.

## Acceptance still open

Ealing/Merton GitHub-hosted collection receives HTTP 403 despite local portal access. Use a permitted collection host/provider feed before activation. Owner's exported review has no scored answers; complete 100-row relevance/currentness/actionability review remains required. W3 9LN/0–5/10 km needs verified 10 activities across three agreed categories/two independent providers; this delivery does not prove it. Three scheduled successful collections over seven days remain unfulfilled. No source activation, merge or production deployment was performed. #39 remains open.

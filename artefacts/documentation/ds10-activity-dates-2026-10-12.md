# Activity date refinements — 12 October 2026

Owner feedback: most worksheet activities have dates available on the website. The downloaded review export currently contains zero scored answers; this feedback is useful evidence, not a completed 90% quality review.

## Repairs

The generic activity cleaner discarded start/end dates for all extraction methods except two library adapters. It now retains valid explicit bounds and individually published session dates for all sources. The extraction schema and prompt request occurrence dates, complete schedules and term-time exceptions. Invalid/reversed dates, contradictory bounds and overlong exact schedules fail with review counters. Recurrence never generates missing session dates. Date bounds do not establish daily attendance.

The public activity mapper also omitted stored start/end fields. The activity detail now displays programme dates separately from the schedule and explains that individual dates/exceptions remain in the schedule. No migration is needed; existing columns are reused.

An opt-in `published_activity_dates` adapter enriches reviewed Oxfordshire/Coventry activity details directly, with matching page title, same-host HTTPS, robots checks and at most four detail pages. Larger directories require narrower routes and fail rather than silently collecting a partial snapshot. These reviewed routes re-read details rather than refreshing from an unchanged root hash; they retain the existing bounded model extraction and can spend one extraction call per source. Other routes gain date retention without automatic additional fetching. No source registry flags are changed.

## Fresh evidence

[Read-only provider-date review](../data/ds10-published-date-review-2026-10-12.json) used fresh public requests HTML, deterministic date parsers and the normal quality cleaner. Other listing fields came from the frozen worksheet; this is not a fresh full model extraction or deployed ingestion. Zero model calls and zero database writes in this check.

- Botley Rhymetime: five explicitly published Friday sessions, 16/23/30 October and 6/13 November, 10–10:30am. The search cache showed older September dates, demonstrating why a fresh provider response matters. Related listing dates are excluded.
- Coventry Tots Time: published bounds 9 July 2026–8 January 2027, every other Thursday, 10–11:15, term time only. No individual dates are generated from the bounds.
- Explore Essex We Are Music: Tuesday term-time wording conflicts with broad calendar dates; it is not a daily session series. No automatic date backfill or accepted extraction is claimed for this source.

117 local Python tests pass, including preserved generic bounds, exact date gaps, invalid-date rejection, related-date exclusion, term-time bounds and robots/title failures. CI type/build checks are required for the display change.

## Remaining

Review booking platform and directory detail routes (ClassForKids, Hoop, HAY, Hertfordshire and remaining worksheet sources) before claiming complete date recovery. This repair does not certify all 100 records. Re-extraction/backfill must be reviewed against current pages before production writes; historical rows remain unchanged. PR #71 and #39 retain their unattended access, pilot, human review and scheduled-repeat acceptance gaps. No source activation/deployment is included.

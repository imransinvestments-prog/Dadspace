# DS10: review of 191 uncertain historical records — 12 October 2026

Owner: Imran Tajuddin. Pilot: W3 9LN, 10 km, ages 0–5 inclusive. Wider-age programmes retained outside pilot. This engineering evidence review does not count as the owner's 100-activity relevance scoring.

## Applied and verified

29 distinct record corrections are live. All 679 original records remain; 650 are untouched. Eight duplicate aliases and one expired Northumberland forest-school series are soft-withdrawn. No source flags or canonical venue IDs changed; first-seen, collection and verification timestamps are preserved. Public feed: 416 → 407 Activities; 163 upcoming Events unchanged. Zero withdrawn rows are public.

Recovered Redbridge's new occurrence accordions with exact published gaps, Southwark's next monthly occurrence rather than its 2024 original start, and Holyrood's selected-date programme bounds. Holyrood individual dates and regularity still need review; bounds do not imply daily sessions. Recovered primary-operator schedules for HonC!, Merry-Go-Round and Shake, Rattle and Roll. Corrected explicit Hoop description clocks/venues without assigning dates from conflicting headers. Retained original metadata on archived duplicate aliases so they remain reversible without colliding with the history-wide identity constraint.

Two We Will Rock You Project links had an unescaped ampersand in venueName. Selecting the actual Edge Theatre venue reveals three classes, all waiting-list entries. Existing provider links are repaired; replacing aggregate rows with bookable classes remains a separate task.

## Scope and evidence

All 191 rows have a recorded disposition, original uncertainty, evidence route, applied patch (where justified) and remaining task. 46 actual ClassForKids root/filter URLs were reviewed through rendered public timetables. 521 standard class rows were observed, including multiple terms, age groups, adult/placeholder rows and waiting lists; this is **not** a count of eligible distinct activities or pilot coverage. Two sample booking links per root are recorded where available; other classes are not implied absent. Two filters have no current timetable rows; this is not proof that the provider has closed. Theatre Peckham exposes camp/exam summaries rather than recurring class rows.

59 distinct non-ClassForKids detail URLs were rechecked: 50 readable, five 404, four NCT access blocks. The NCT rows were already withdrawn. 16 observed primary/booking routes were also checked (15 readable; Milton Country Park's old programme route 404). Raw HTML and full before/after backups remain local; published evidence contains route/status/hash metadata and factual review summaries.

## Remaining active follow-ups: 173 records

- 82 provider summaries need exact class/venue/age/term/availability mapping; two repaired ClassForKids records are also among the corrected records with follow-ups.
- 39 records lack detail links; source-index titles or city labels cannot establish session identity. Keep Baby Bells/Beeps, different ages, branches and clock times separate.
- 32 records need programme-specific evidence: multi-centre schedules, library catalogues, provider-wide dance summaries, mobile 1:1 coaching, or source date/time contradictions.
- Five detail routes need recovery via current operator navigation, without treating a 404 as programme closure.
- 15 corrected records retain follow-ups, including the two venue links, Hoop programme/date associations and Holyrood's individual booking dates/regularity.

Five active rows are corrected with no remaining metadata task in this cohort; eight aliases and one expired series are withdrawn; four were already withdrawn. These categories sum to 191 and do not claim all uncertainties resolved.

Use [the searchable review worksheet](ds10-uncertain-191-review-2026-10-12.html) or [the full record ledger](../data/ds10-uncertain-191-review-2026-10-12.json). [ClassForKids evidence](../data/ds10-uncertain-classforkids-evidence-2026-10-12.json) and [source access checks](../data/ds10-uncertain-source-checks-2026-10-12.json) are separate.

## Validation and limits

127 local tests pass, including published occurrence gaps/mixed-venue rejection and guarded URL/provenance checks. Forward SQL passed a transaction rollback rehearsal before application. Fingerprint guards protect concurrent changes and every applied field was checked against the after snapshot. Full undo batch is retained locally and rehearsed with rollback. New Redbridge parser support is in draft PR #71; it is not merged/deployed. Reviewed explicit date backfills are protected by the earlier live guard; undated timetable/location edits can still be changed by future ingestion until the relevant adapter repair is released. No new source activation, deployment, owner scoring or seven-day scheduled-run evidence is claimed.

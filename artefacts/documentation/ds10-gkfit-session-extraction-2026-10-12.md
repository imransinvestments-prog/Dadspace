# GK Fit individual session extraction

Reviewed 12 October 2026. Owner: Imran Tajuddin.

The adapter follows the HAY listing's observed operator link, then the operator's visible navigation to its booking catalogue, daytime timetable, netball timetable and holiday programme. Public-page robots rules permit these routes. This is HTTP extraction of public HTML, without browser snapshots, private APIs, model calls or booking submissions.

The current [booking catalogue](https://www.gkfit.co.uk/book) has 19 service cards. Eleven proposals were generated:

| Programme | Venue | Proposals |
|---|---|---:|
| Multisports, age 5–8 and 9–12 | Meadows Community Centre | 2 |
| Dodgeball, age 5–8 | Hauxton Centre | 1 |
| Netball, school years 7–11 | Girton Rec | 1 |
| Netball, school years 9–11 | Netherhall School | 1 |
| Multisports, age 5–8 and 9–12, Nov–Dec | Royston Leisure Centre | 2 |
| Game Night, school years 6–8 and 9–11, 22 October 2026 | Netherhall School | 2 |
| Holiday netball, age 11–15, 27 and 30 October 2026 | Cherry Hinton Leisure Centre | 2 |

Eight cards were excluded: four age-specific classes explicitly marked full on the timetable, and four Game Night occurrences marked ended in the current catalogue. In particular, the live catalogue marks both 13 October games ended even though that date is after this review date. The provider's explicit status takes precedence; those contradictions are retained in the review issues. A full weekly Netherhall class does not make its separately booked Game Night full.

The [daytime timetable](https://www.gkfit.co.uk/daytime) supplies venue addresses and describes home-educated/out-of-school eligibility. The Nov–Dec Royston catalogue has different times from the older September–October timetable: current course-card times are preserved. Its year and end dates are not explicit, so no dated occurrences are generated. Booking links identify each actual service. Catalogue course prices are captured separately from advertised per-session prices; remaining-course prices must not be presented as per-session prices.

Recurring courses remain Activities. Game Night is a dated occurrence of a recurring programme. Holiday programme classification remains a review item because dates alone do not establish rare-event status. School-year bands remain school-year bands. Useful wider ages and venues outside the pilot are preserved. Published course start labels and term lengths are retained in notes/schedules; a term length does not generate an end date or individual weekly occurrences.

Little Skills is advertised for interest registration without a venue/time. Mobile, private and small-group coaching are arranged on request. No individual sessions are invented for these offerings. Booking-card presence and “Loading availability” do not confirm remaining places. All proposals require review before live application.

`coverage_complete` refers to handling the current 19-card booking catalogue, including documented exclusions. It does not mean every operator offering has an actionable timetable, nor that the production worker is configured. No source activation, live insert, aggregate withdrawal or deployment occurred.

Run this programme alone, preserving other parents:

```powershell
python scripts/collect_ds10_session_proposals.py --as-of 2026-10-12 --record-id d439f22f-6a3a-4bb2-ac1e-1bb941d1cbef
python scripts/build_ds10_action_console.py
```

Evidence: `artefacts/data/ds10-gkfit-extraction-2026-10-12.json`, plus the combined session-proposal report. The current batch made six public-page requests, with normal robots checks and existing request budgets. Other parent records were verified unchanged. The combined report contains 132 distinct proposals. The console contains 154 prefilled rows across its parent records, including shared library rows.

Validation: 142 Python tests passed. GK Fit tests cover real factual catalogue fixtures, dated versus recurring courses, ended/full exclusion, independent Game Night eligibility, newer Royston times, missing addresses, unsafe booking routes and unrecognised catalogue structure. Console validation and inline script syntax checks passed.

Refresh the local action console, select **Sports Coaching Sessions for Children – GK Fit**, and use **Add generated proposals to this draft** to merge them into an existing draft while preserving edits.

Next: Scouts in South Cambridgeshire, then Shredder Skate School, separately.

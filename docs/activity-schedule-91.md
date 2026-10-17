# Activity schedule contract and review (#91)

## Boundary and implementation

Read/display change only: no database writes, migrations, eligibility/freshness
changes, recurrence expansion or new source calls in the public read path.
`recurrence` now survives the existing public mapper. A shared pure interpreter
and display component cover Activities list, detail and related cards. Existing
description, price, age and source links are preserved; raw schedule and stored
date bounds remain in detail, without calling every bound a programme lifetime.

Supported explicit occurrence formats are the existing `Published dates:` and
`Published session:` ISO output plus a single stored occurrence. A date range
alone is not expanded into daily sessions or treated as programme validity.
Coventry's existing reviewed adapter copies a source-explicit `Date: … Recurs`
programme period: require the official detail URL and exact agreement between
copied English dates and stored bounds before interpreting that period.
Unknown formats remain unconfirmed; conflicting/invalid dates remain unclear.

Dates use Europe/London today; date-only values do not imply a same-day session
is still ahead. No time is invented. Source-reported clocks are displayed as
supplied, not guessed timezone conversions. Recurrence alone does not certify
current operation. After the final listed occurrence, show next date unconfirmed,
not programme ended. Source-explicit programme expiry uses separate wording.

## Fixed owner review pack: five actual records

Snapshot: `artefacts/data/activity-schedule-review-2026-10-16.json`. Interpret as
of 16 October 2026; live previews roll forward with the London date and may use
newer source data. This is one bounded wording/evidence review, not 100-activity
quality acceptance or a complete catalogue audit.

| Record | Stored evidence | Expected interpretation on 16 October |
|---|---|---|
| Carterton: Rhyme Time | Recurring; only 13 October listed; Tuesday time supplied | Keep discoverable, show published pattern and past listed dates; next published session unconfirmed. Do not assert ended or generate 20 October. |
| Henley: Stay and Play | Single stored 17 October occurrence; 10–11am | Next listed session 17 October, source-supplied time; not a promise of availability. |
| Henley: Rhymetime | Explicit 19/26 October and 2/9/16 November list | Next listed session 19 October; choose only remaining published dates as time advances. |
| Baby Gym (Salford) | Recurring; no dates, schedule or time | Regular activity; next published session unconfirmed. |
| Tots Time (Coventry) | Explicit 9 July 2026–8 January 2027 period; fortnightly Thursday, term-time | Show source-explicit period and restrictions; no generated next fortnightly date. |

**Sixth case is a controlled test, not another real ended record:** evaluate the
same Tots Time evidence on 9 January 2027; label its published programme period
ended. This does not assert that it has ended today or that the operator ceased.

Owner questions: is the distinction clear, does the compact summary preserve the
evidence without implying validity/availability, and are unknown/conflict states
honest? Full source details remain available. No new general review UI is built.

## Discovered dependency and wider consumers

Retrieved Oxfordshire source material lists later Carterton dates than the
stored snapshot. Reverify current operator evidence before any correction;
cached web material does not itself authorize a production backfill. Track the
bounded source/row discrepancy under #135. This patch deliberately does not
insert dates from a web lookup or hide a continuing activity due to old dates.

Home's `activeThisWeek` and nearby-week count independently use date/recurrence
eligibility. Their semantics, geography and public counts are unchanged here;
regress them, but do not claim this display patch fixes their independent policy.
Any separate correction needs explicit scope and evidence.

## Verification, rollout and rollback

Regression cases cover past recurring occurrences, real gaps, missing/invalid/
conflicting dates, source-explicit bounds and end, London midnight/DST, same-day
uncertainty and actual rendered summary. Preserve existing public failure,
radius/paging and Home contracts. Preview uses existing detail/list routes.

Owner preview/release approval is required before merge. Verify the five real
detail examples, list/related cards and retained source evidence. After approval,
deploy and read back production before closure. Rollback reverts the app commit;
no database recovery is needed. #93 still owns wider cost/age/card improvements.

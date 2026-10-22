---
name: new-source-adapter
description: Scaffold a new Dadspace activity/event source adapter with fixtures and unittest coverage, following the discovery model. Use when adding a new provider, timetable, library portal or calendar source.
disable-model-invocation: true
argument-hint: <provider name> <source URL>
---

# New source adapter

Add an adapter for: $ARGUMENTS

## 1. Read first
- `docs/discovery-model.md`: the owner's definitions. Venues are places, Activities are regular opportunities, Events are infrequent occasions.
- A similar existing adapter and its test, for example `gkfit_sessions.py` + `tests/test_gkfit_sessions.py` (multi-page Wix timetable) or `session_proposals.py` (`parse_spydus`, library occurrences).
- How adapters are wired in: `scripts/collect_ds10_session_proposals.py`.

## 2. Check access before writing a parser
- Find the real operator host and its family/detail pages. Cookie consent, JavaScript, redirects or detail-page navigation can hide valid programmes from plain HTTP. An inactive-looking source is not an unsuitable one.
- Record access and republication limits separately from usefulness.

## 3. Capture fixtures
Save the real pages to `tests/fixtures/<provider>/` (`.html` or `.json`). Tests run against fixtures, never the live site.

## 4. Write the adapter (`<provider>_sessions.py` or `<provider>_calendar.py` at repo root)
Match the existing adapter style: a pure `parse_<provider>(...pages, today)` returning `(items, issues)`.
- Build items with `session_proposals.proposal(...)` and links with `public_link(...)`. Reject foreign hosts and non-https routes.
- **Never invent data.** No inferred locations, dates expanded from weekdays, or end dates derived from term length. Missing venue, weekday, time or age goes into `issues` with a reason, or a note saying review is needed.
- **Classify from regularity evidence.** A date, ticket link, booking requirement or museum/library source does not make something an Event. A dated occurrence can belong to a regular Activity. Keep both the occurrence dates and the recurring schedule. Ambiguous cases get a review note, not a guessed numeric threshold.
- An unmatched venue must not drop an otherwise useful listing. Reuse canonical venue names; don't create a place per session.
- Exclude past dated occurrences (`< today`) and provider-marked ended/full classes, with an issue reason.
- Raise `ValueError` when the expected page structure is missing, so a broken source fails loudly instead of yielding zero.

## 5. Tests (`tests/test_<module>.py`, `unittest`)
Cover at least:
- expected item and issue counts against the fixture, with a fixed `today`
- distinct `proposal_key`s
- past occurrences excluded when `today` moves forward
- missing structure raises `ValueError`
- foreign booking links rejected, and missing addresses not inferred

Run: `python -m unittest discover -s tests -p test_<module>.py -v`

## 6. Wire up and report
- Register the parser in the collection script, and in a workflow under `.github/workflows/` if it needs its own CI test step.
- Summarise: items, issues by reason, the Activity/Event classification evidence, and any access limits found.

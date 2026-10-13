# DS-09 matrix reconciliation — 11 October 2026

All 155 original source IDs are reconciled against the 135-source follow-up and 20 healthy exclusions. The machine matrix and source table are the current recommendations. Original decisions and reasons are preserved separately for traceability; raw access, yield and registry snapshots remain historical evidence.

**Confirmed scope:** W3 9LN, ages 0–5 inclusive, 10 km radius. **Named accountable owner:** Imran Tajuddin, for content review and technical upkeep. Engineering implements adapters.

## Current decisions

| Decision | Sources | Meaning |
| --- | --- | --- |
| Keep | 20 | Retain healthy operation; no follow-up fetch or adapter changes. |
| Improve | 101 | Qualify or repair actual programme routes. Inactivity and access failure alone are not suitability verdicts. |
| Replace | 27 | 23 committee calendars plus four generic venue/operator discovery roles; preserve independent venue-discovery value. |
| Pause | 7 | Explicit robots, approved-access, redundant-route or sector-training blockers. |

## Original → reconciled

| Original | Reconciled | Sources |
| --- | --- | --- |
| improve | improve | 69 |
| improve | keep | 20 |
| pause | improve | 32 |
| pause | pause | 7 |
| pause | replace | 4 |
| replace | replace | 23 |

## Remaining pauses

- **ClassForKids**: Generic route is redundant with configured per-city sources. Keep paused to avoid duplicate collection; follow-up readability does not reverse this reason.
- **Federation of City Farms and Community Gardens**: Existing public events role is sector training/networking rather than family programmes. Retain as operator discovery, with no automatic activation.
- **Hoop**: Generic route is redundant with configured per-city sources. Keep paused to avoid duplicate collection; follow-up readability does not reverse this reason.
- **NCT Local Activities & Meet-ups**: Useful family programmes, but the explicitly unresolved approved data-access/republishing route remains a blocker. Follow dedicated branch/detail adapter requirements before enabling.
- **Lancashire County Council**: Latest robots evidence disallows collection of this route. Seek a permitted organiser export/API or replacement; do not bypass.
- **Manchester City Council**: Latest robots evidence disallows collection of this route. Seek a permitted organiser export/API or replacement; do not bypass.
- **The Wildlife Trusts**: Latest robots evidence disallows collection of this route. Seek a permitted organiser export/API or replacement; do not bypass.

## Access and delivery boundaries

Original HTTP access stays in access_status; newer bounded follow-up access is stored separately in follow_up_access_status. The recommendation, access state and production active flag are independent. All source-specific next actions are carried into the matrix; useful operator alternatives do not erase robots or republishing restrictions.

Content quality, republishing permission and per-source maintenance cost remain unqualified where evidence is missing. These unknowns are recorded rather than silently accepted. #39 delivers adapters and repeated collection, #40 canonical venue matching, #32 scheduling/health and #70 the upkeep UI. Radius and named-owner questions are resolved. #38 audit acceptance and PR review/merge remain open; this reconciliation does not declare the feeds operational.

[Reconciled source table](ds09-source-decisions-2026-10-10.md) · [London collection plan](ds09-london-collection-plan-2026-10-10.md) · [Original decisions](../data/ds09-original-decisions-2026-10-10.json)

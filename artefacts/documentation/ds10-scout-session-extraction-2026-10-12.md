# Scouts in South Cambridgeshire — individual section extraction

Owner: Imran Tajuddin. Reviewed 12 October 2026.

The 21-group HAY inventory now has a reviewed route manifest and deterministic public-HTML extraction. A bounded collection produced **51 distinct section/meeting proposals from 16 groups**, with **25 public-page requests** and normal robots checks. All other parent records were verified unchanged. The combined proposal report now contains 183 distinct proposals; the action console has 205 prefilled rows across its parent records, including shared library rows.

| Group | Proposals |
|---|---:|
| Milton & Landbeach | 4 |
| Orchard Park | 3 |
| Whittlesford & Duxford | 2 |
| Fulbourn | 4 |
| Over | 2 |
| Willingham | 4 |
| Swavesey | 3 |
| Northstowe | 3 |
| Cottenham | 4 |
| Oakington | 3 |
| Bar Hill | 4 |
| Hardwick & Highfields | 3 |
| 1st Cambourne | 3 |
| Bourn | 3 |
| Comberton | 3 |
| 2nd Cambourne | 3 |

The [Crafts Hill group pages](https://craftshillscouts.org.uk/1st-northstowe/) publish section-specific age bands and meeting times. Individual sections and multiple meeting nights are preserved. Bar Hill, Cottenham and Fulbourn publish Squirrels for ages 4–6. These overlap the pilot age band but are outside its London geography. Useful older-age sections remain included. Membership enquiries are required; a published meeting time does not confirm spare places.

The [Orchard Park district page](https://www.cambridgescouts.org.uk/groups/1stcambridge/) publishes three Friday section times. Its ages come from the explicitly identified county section reference, rather than from the area-wide 4–25 description. Milton's section pages preserve their own age wording and term-time meeting rules. Fulbourn's Beaver heading says 7½–8½ while its body describes 6–8; both statements are preserved for eligibility review.

Five groups have no proposed sessions:

- Waterbeach: only historical 2021 times were found; a contemporary primary timetable is needed.
- Shelfords and Stapleford: the [membership page](https://www.shelfordsandstaplefordscouts.org.uk/join/) explicitly says all sections are full. This remains a waiting-list opportunity rather than an available session proposal.
- Sawston: an older operator page gives St Mary's Community Hall, Church Lane, rather than the HAY High Street pin. Current section times and the venue need confirmation.
- Caldecote: no current primary section timetable has been qualified.
- Barton: HAY identifies **7/16 Cambridge**, while Crafts Hill identifies **6/17 Cambridge**. The timetable is not attached across that identity discrepancy.

Other exclusions: Over's Beavers are explicitly unavailable; Whittlesford & Duxford reports waiting lists for its non-Beaver sections; Milton advertises Squirrels without meeting times. Duxford's two named Beaver colonies remain separate proposals. No dates, section availability or future meetings are invented for excluded offerings.

HAY currently returns HTTP 403 to the collector. The manifest's address inventory comes from its previously reviewed public HTML, corroborated by the accessible directory evidence during this review. Every proposal explicitly flags the address as provisional and requires confirmation of the section's actual meeting place. Current timetable pages are fetched directly from reviewed public operator/district routes. No access-control bypass, protected membership system, contact submission or provider message is used.

These are recurring Activities. Dates remain blank; published weekday/time patterns are preserved. Term-time restrictions are retained where actually published. No canonical venue is created or matched automatically. Source access, useful programme evidence and venue qualification remain separate. `coverage_complete` remains false because unresolved groups and venue/eligibility checks remain.

Replay Scouts alone:

```powershell
python scripts/collect_ds10_session_proposals.py --as-of 2026-10-12 --record-id dd4e8663-1d52-49ba-a7c1-edd1f1d93c65
python scripts/build_ds10_action_console.py
```

Evidence: `artefacts/data/ds10-scout-group-routes-2026-10-12.json` and `artefacts/data/ds10-scout-session-extraction-2026-10-12.json`. Implementation: `scout_sessions.py` and the existing single-programme proposal collector. The route manifest is deliberately bounded; new groups or changed page layouts require qualification rather than guessed routes or unsupported inference.

Validation: **147 Python tests passed**, covering section ages, multiple meeting nights, named colonies, unavailable/wait-list exclusions, conflicting eligibility, plural age headings and isolated route failures. Console validation and inline JavaScript syntax checks passed. No live database writes, source activation, aggregate withdrawal or deployment occurred. Human relevance review remains outstanding.

Refresh the local action console, select **Beavers, Cubs & Scouts in South Cambridgeshire**, and click **Add generated proposals to this draft** to merge these rows into an existing draft while preserving edits.

Next programme: Shredder Skate School.

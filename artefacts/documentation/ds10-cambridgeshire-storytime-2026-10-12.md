# Library.Live Storytimes for Under 5s — session extraction

Owner: Imran Tajuddin. Reviewed 12 October 2026.

The council's current [Storytime directory](https://info.cambridgeshire.gov.uk/kb5/cambridgeshire/directory/results.page?qt=storytime&term=&camcommunitychannel=6-4&sorttype=relevance) contains 16 matching service listings across two pages. Each observed detail page was reviewed in the browser. The original Library.Live route redirects without preserving the search.

The offline parser now produces 16 branch/session proposals with published weekday patterns, times, ages where supplied, costs and attendance restrictions. Monthly, weekly, term-time and fortnightly schedules remain distinct. Recurring programmes remain Activities. Wider ages are preserved: the programme heading does not override individual published eligibility. No dated occurrences are invented from a weekday pattern.

Arbury Court and Cambourne are mixed Storytime/Rhymetime programmes already represented by the Rhymetime extraction. Their stable proposal identities are shared across the two parent records. This adds 14 distinct proposals, bringing the combined report to 121. The console contains 143 prefilled rows across its parent records, including shared programme rows. Existing drafts can use **Add generated proposals to this draft**; this preserves edits and avoids repeated additions. Refresh the local console to load the new evidence.

Six evidence flags remain across five listings:

- Huntingdon: published branch name but no street address/postcode.
- Ely: no published age band; fortnightly dates require confirmation at the library.
- Cherry Hinton: fortnightly dates require verification against the linked Eventbrite organiser listings. The organiser link is preserved; it is not treated as an individual booked occurrence.
- Cambridge Central Monday and Sunday: age fields differ from descriptions specifying 18 months to 5 years. Both statements remain visible in proposal notes for resolution before application.

Littleport requires booking at the library desk and has extremely limited places. Bar Hill publishes age 4+ and describes key stage one children; both facts are preserved. Fulbourn's eligibility extends to age 6 and Littleport's to age 11. These useful listings remain available rather than being narrowed to the pilot band.

The provider's robots rules disallow unattended access for the Dadspace collector. This work enables deterministic offline extraction from explicitly reviewed public-browser snapshots. It does not qualify or activate scheduled crawling. A permitted feed or provider-authorised route remains required. Directory pagination coverage is complete for this snapshot; ongoing collection coverage remains false.

Replay one programme without contacting the website:

```powershell
python scripts/collect_ds10_session_proposals.py --as-of 2026-10-12 --record-id bbc6d669-367b-4eb4-9cde-18372c8afe77
python scripts/build_ds10_action_console.py
```

Evidence: `artefacts/data/ds10-cambridgeshire-storytime-snapshot-2026-10-12.json` and `artefacts/data/ds10-cambridgeshire-storytime-extraction-2026-10-12.json`. The collector preserves the other programmes. Imports and replays merge shared proposal keys and are repeatable.

Validation: 139 Python tests passed, including programme-origin checks, unsafe-link rejection, actual schedules/age conflicts, shared identities, repeated import and preservation of all other parent records. Console validation and inline JavaScript syntax checks passed. Single-programme replay made zero public-page requests. No live database writes, source activation, aggregate withdrawal or deployment occurred. Human relevance review remains outstanding.

Next programme: GK Fit, followed separately by Scouts in South Cambridgeshire and Shredder Skate School.

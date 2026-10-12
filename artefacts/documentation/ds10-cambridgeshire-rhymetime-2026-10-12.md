# First programme: Library.Live Rhymetimes for Babies and Toddlers

The snapshot extraction adapter now creates **31 session proposals** from **33 observed public council detail pages**. Four search-result pages were inspected through normal browser navigation, followed by each observed service link. The owner can load these proposals in the existing action interface instead of typing sessions.

## What was recovered

Each proposal retains the named branch/place, street address/postcode where published, age band, programme weekday/frequency, exact hours, term-time restrictions, cost and source detail link. Baby/toddler groups remain separate. Cambridge Central's two Thursday groups retain their different times and service identities. Cottenham's two-week pattern and Histon's first/third-Thursday schedule remain intact; no future dates are generated from recurrence. Soham's ages come from the published introduction because its structured age field is absent.

Two programmes are held rather than assigned a misleading normal library address: Wisbech uses alternative locations during partial closure; Whittlesey's Wiggle and Giggle programme has a temporary Peel House venue and differing legacy hours. These need the provider's date-specific temporary schedule. The two Huntingdon proposals have published times/ages but no street address/postcode on their detail pages, so branch matching remains flagged. Neither a failed route nor an excluded session establishes programme closure.

## Access limitation

Library.Live's old `www.cambridgeshire.gov.uk/directory?...` locator redirects to a generic directory homepage and drops its query. The [current council Rhymetime search](https://info.cambridgeshire.gov.uk/kb5/cambridgeshire/directory/results.page?qt=rhymetime&term=&camcommunitychannel=6-4&sorttype=relevance) was reached using the council's linked directory and its visible search form. Essential-cookie consent is sufficient for browser reading.

The directory's `robots.txt` disallows wildcard automated access; do not impersonate the separately allowed crawler or bypass this rule. This delivery supports **offline parsing of public browser-review snapshots**, not a qualified unattended feed. The scheduled collector does not fetch the disallowed directory; it parses the saved reviewed snapshot and visibly retains the access limitation. A permitted provider export/feed or access arrangement remains required for unattended refresh. Coverage of the inspected index is recorded separately from live-source qualification; the aggregate cannot be automatically retired.

## Use and replay

Refresh [the action interface](ds10-action-console-2026-10-12.html), open **Rhymetimes for Babies and Toddlers**, and choose **Add generated proposals to this draft** if a browser draft already exists. Existing drafts remain intact. Generated data is unapproved; no live listings, venue identities or source flags changed.

`scripts/collect_ds10_session_proposals.py --record-id 368a7430-a54b-4c02-9af7-0d4702d740dc --as-of 2026-10-12` replays this programme alone with zero network/model/database calls. It preserves other programmes' proposals. Then run `scripts/build_ds10_action_console.py` to rebuild the standalone interface. The explicit snapshot import is `scripts/import_ds10_rhymetime_snapshots.py <snapshot.json>`.

[Observed factual snapshots](../data/ds10-cambridgeshire-rhymetime-snapshot-2026-10-12.json) and [extraction results with exceptions](../data/ds10-cambridgeshire-rhymetime-extraction-2026-10-12.json) record provenance. The combined review has **107 distinct proposals**; repeated historical Storytime parents are not double-counted.

135 Python tests pass, including real-snapshot counts, distinct same-branch groups, recurring schedule restrictions, relocation exclusion, missing-clock rejection, foreign/unobserved links, duplicate/incomplete snapshots, published age fallback and missing-address flags. Console import/export validation and JavaScript syntax checks also pass. The next programme in the requested sequence is Library.Live Storytimes for Under 5s; its extraction is unchanged in this delivery.

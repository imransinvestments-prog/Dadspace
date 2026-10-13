# Automated session proposals

The selected 11 aggregate records no longer require manually typing every session. The read-only collector parses Hertfordshire Spydus occurrence cards and observed pagination, Mini Athletics venue/class tables and HAY Cambridge's five-centre stay-and-play timetable.

The current bounded run generated **76 distinct proposals across six original records**: 20 Baby Rhyme Time occurrences, 20 Storytime occurrences shared by two historical aggregate rows, 20 LEGO occurrences, 11 Mini Athletics classes and five stay-and-play programmes. The interface displays proposals under both Storytime aliases, but the shared proposal keys prevent them being counted as separate opportunities in the report. School-only eligibility, full/waiting-list exclusions, half-year age bands, term-time restrictions and source evidence are retained. Rolling/term bounds are not expanded into invented occurrence dates.

The library catalogues contain additional pages. This run reads up to two pages per catalogue and flags partial coverage. Existing aggregates must remain until replacement coverage and canonical identities are reviewed. Two full/waiting-list Mini Athletics classes are excluded from bookable proposals. Empty age/address fields are evidence gaps, not instructions to invent values. Programme classification and pilot acceptance remain separate.

Five records still need a supported detail route/adapter: Library.Live Rhymetimes and Storytimes (Cambridgeshire directory), GK Fit, South Cambridgeshire Scout groups and Shredder Skate School. Their observed routes are listed as exceptions; the user is not asked to invent these sessions. No failed or incomplete route is declared successfully empty.

Open the refreshed [action interface](ds10-action-console-2026-10-12.html). Existing browser drafts are preserved. Select **Add generated proposals to this draft** to merge proposals into an older saved draft. Review the source and mark the aggregate decision ready, then export decisions for checked application. Generated proposals are not owner approvals and do not substitute for the separate human relevance sample.

## Repeating the collection

Run `scripts/collect_ds10_session_proposals.py --as-of 2026-10-12 --max-pages 2` with repository Python dependencies, then `scripts/build_ds10_action_console.py`. The collector checks public robots rules, caches repeated URLs, restricts observed pagination to the same host and fails on malformed/unsupported dates or incomplete timetable layouts. Network call attempts are bounded at 50, including robots and failed attempts (HTTP redirect exchanges are handled by the requests client). No guessed IDs, model calls, database writes, source activation or aggregate withdrawal occur.

Full run evidence and proposal-to-original-record mapping are in [the generated data](../data/ds10-automated-session-proposals-2026-10-12.json). Readable source pages are not a completeness or quality guarantee. Stable library proposal identities use the published record number rather than transient search-session tokens.

Validation: 131 Python tests pass, including unstable catalogue-token replay, pagination detection, stale-date rejection, rolling schedules, half-year ages, full-class handling and incomplete centre-table rejection. The console's Node checks verify the 19-record cohort, evidence validation, guarded imports, source fingerprints and inline-script syntax. The implementation is local and has not been deployed.

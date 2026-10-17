# Sprint 3 — Places data accuracy

Tracker #171; tickets #162 and #100. Provisional direct effort: #162 2 points,
#100 3 points, total 5. No extra tracker points or date promise.

## Correction proposal

Freeze: 17 October 2026, Dadspace production. Current cohort has **3,440 public
libraries**, not the historical 3,403. Frozen UUIDs and whole-row database MD5
fingerprints are recorded in `artefacts/data/places-data-cohort-2026-10-17.json`.

- **#162:** The Little Garden Nursery (`4437eb40-96da-4548-935f-a0a22c9ad7ff`)
  changes from Children’s playground to `nursery`, with publication switched off.
  Access remains NULL/unknown; no assertion of private or public entry. Existing
  name, approximate address, coordinates and source URL stay unchanged. Owner's
  16 October correction supersedes the generic 14 October playground-access
  restoration for this misclassified row. Nursery identity is corroborated by
  [Ofsted](https://reports.ofsted.gov.uk/provider/16/2516013); this does not validate
  the imported W3 7LH address, and no address correction is included.
- **#100:** 3,392 libraries acquire **England** attribution. **48 stay unknown**:
  33 postcodes returned no current match; 15 records have no postcode. Scotland,
  Wales and Northern Ireland each have zero in this frozen production cohort.
  This is not a claim of complete UK library coverage. Publication stays true for
  all 3,440 libraries. No hours, entry/access, fees or coordinate enrichment.

Owner explicitly authorized transmitting library postcodes to Postcodes.io in
chat. The collection sent only postcodes in batches of at most 100. A prior
automatic-review rejection was respected until that authorization arrived.
The cached response is evidence from a point in time, not proof of current
library operation. Unknown/closed/moved supply is outside this nation's fix.

## Verification and import persistence

Resolver requires normalized exact postcode, a supported returned nation and a
matching nine-character GSS administrative district code. If a retained source
authority code conflicts with the returned nation, attribution stays unknown.
Names and postcode-area prefixes are never used to guess nation.
[Postcodes.io bulk API](https://postcodes.io/docs/postcode/bulk/) and the
[ONS England geography hierarchy](https://www.ons.gov.uk/methodology/geography/ukgeographies/administrativegeography/england)
document the input and code conventions. Retained source provenance IDs and the
lookup date/reason are linked per row. Real lookup fixtures cover England,
Scotland, Wales and Northern Ireland.

Active importer is `.github/workflows/venue-reference.yml` →
`venue_reference_loader_v2.py`. The importer fills missing countries, preserves
existing values and stores namespaced `_dadspace_country` evidence without
discarding source fields. API failures produce explicit unknown reasons.
Push-triggered imports now default to dry run, preventing a code merge from
silently applying a national data change. Explicit workflow write runs remain
available after review; no workflow was dispatched by this sprint.

The existing operations trigger does not protect category/country. A supplemental
invoker trigger protects category on operations-reviewed rows and country where
accepted per-record geography evidence exists. It does not mark every other
library field reviewed or freeze unrelated enrichment. No new table, public API,
RLS grant, provider or source activation is required. The existing review override
is used only inside the explicitly reviewed correction transaction.

## Deployment and recovery

1. Review code, exact correction totals, 48 unknown rows and nursery hold.
2. After owner approval, deploy the protection migration, run the generated SQL
   with its default **ROLLBACK**, verify counts and guards, then apply the same
   reviewed plan with an explicit COMMIT. Any row/cohort drift stops the run and
   requires a rebuilt preview. No partial live application.
3. Verify actual database counts, changed fields, persistent provenance, import
   attempts and public nursery removal. Only then close tickets.

`scripts/build_places_data_review.py` reproduces JSON/CSV/HTML and guarded SQL.
The data transaction snapshots before-images in separate `venue_sources` audit
records and checks only allowed columns changed. It refuses existing audits or
stale/missing fingerprints. Library count/membership is rechecked before writes.

The rollback SQL checks after-fingerprints before restoring fields, retains audit
history with acceptance false, and defaults to ROLLBACK. Execute recovery only
with owner authorization. To undo schema after data recovery, drop the supplemental
`venues_preserve_reviewed_geography` trigger and its function; the original
operations protection is left intact. No irreversible deletion is proposed.

## Current evidence and remaining gate

Seven targeted offline tests and Python compilation passed. Tests cover the real
four-nation fixtures, missing/mismatched/conflicting results, network failure,
deduplication, preserved source evidence, repeat-import preservation, reconciliation
and correction SQL guards/default rollback. No persistent production data or
schema changes have been made. Transactional SQL and real trigger readback are
required after approval before commit; unit tests do not claim to prove them.

Human review is one nursery decision plus the nation totals/unknown policy, not
3,440 manual labels. The CSV contains every record; the HTML lists all 48 unknowns.

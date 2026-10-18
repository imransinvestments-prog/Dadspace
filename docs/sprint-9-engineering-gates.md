# Sprint 9 engineering gates

Owner approval is recorded on #197/#40/#104/#133/#198 and PR #201. No repeat policy/source/cadence approval is required within that reviewed scope. This engineering implementation does not invent new place mappings or enrol a provider whose hosted route is inaccessible.

## Actual identity integration

`library_portal_sessions_v1` is an explicit opt-in adapter for the two reviewed Ealing numeric series. Other adapters retain their existing policy. The real parser groups by the qualified host/session ID; the real cleaner preserves explicit occurrence IDs/URLs/dates/times and creates a stable session key. Distinct series survive identical titles/venues; a rename within one series keeps the same key. Malformed, duplicate, out-of-scope or unqualified metadata fails closed. No programme above those series is inferred.

CLI-generated migration `20261018213916_reviewed_provider_session_identity.sql` adds optional metadata, a service-readable/admin-managed enrolment table, database validation, same-session transaction locking, immutable provider binding and append-only provenance audit. The enrolment table starts **empty**. The reviewed existing-row adoption cohort is also empty, so importer adoption of an existing legacy row is rejected; no unseen historical mapping is authorised. New provider rows require both the opt-in adapter and an explicit matching database enrolment rule. Enrolment grants no additional client/public access.

The migration reuses the actual identity trigger and operations review API. Legacy rows keep their original review fingerprints despite new nullable columns. Existing reviewed canonical relationships remain protected on subsequent imports; provider place/retirement changes require the existing reviewed operation. Audit history retains before/after row facts, listing UUID, provider binding and occurrence provenance. New metadata does not change the public view projections.

`rollback-provider-session-identity.sql` is a transaction-locked inverse only for an unchanged empty-enrolment release. It verifies installed function/trigger fingerprints, zero enrolled sources, zero provider rows and zero provider audit history, then restores captured original definitions. After any provider adoption/write or intervening implementation change it refuses to discard history; a separate reviewed inverse is required. No production rollback has been performed.

## Verification

The committed worker-payload fixture is regenerated through the actual parser and cleaner and compared by Python tests. PostgreSQL-compatible local tests execute the real migration, actual review/link/rollback RPCs, actual import payloads and existing operations transaction suites. They verify legacy fingerprints, rename continuity, distinct sessions, dedupe conflicts, source/session/place/retirement guards, protected reviewed relationships, durable provenance and stale inverse refusal.

The dedicated hosted gate uses a disposable PostgreSQL 17 service and independent connections. It observes the second same-session connection waiting on a real lock, checks one retained listing for concurrent same-session imports, two listings for concurrent distinct sessions, provenance records, nonempty inverse refusal and clean empty inverse. It has no production credentials, database connection or model calls. Hosted results belong to the exact PR SHA and are recorded in #197/#198.

The normal MyLibrary source workflow is unchanged in scope: shared-worker changes still test Ealing, Merton and Sutton. A hosted HTTP 403 remains a failed source/release gate, even if normal local HTTP produced usable provider fixtures. No proxy, challenge bypass or test suppression is introduced. Library route recovery stays #134; no provider is enrolled/activated until that route is qualified.

## Release sequence

1. Pass local integration and real PostgreSQL concurrency/inverse checks; preserve all required hosted checks and actual source failures.
2. Merge/release only after the remaining required checks pass. Apply the additive empty-enrolment migration transactionally, verify zero enrolments/adoptions and public/legacy behaviour, then deploy the coordinated worker capability. Do not activate an old collector against a newly enrolled source.
3. Re-read the approved exact Hounslow/NCT registry fingerprints and source evidence. Complete bounded dry passes, approved configuration, controlled activation and stored/public readback independently. NCT still needs its own identity/classification validation; Ealing session identity is not silently assigned to NCT nodes.
4. Record each actual release/configuration boundary for #125/#132/#129. Scheduled observations retain their criteria and are not replaced by these tests/manual runs. Final place mappings and #135 historical corrections remain separate from installing this capability.

## NCT publication hold

The read-only NCT candidates are individual dated occurrences. Publishing them through the old title/place key would coalesce them and leave only the final occurrence's bounds. Live publication is therefore explicitly rejected before any listing write; enabling the schedule variable and registry row cannot bypass this gate. The 30-day dry-run/health/routing controls remain testable, but #104 is not ready for activation or closure.

A current normal, robots-permitted check found useful primary evidence: the Alf King occurrences booked under Eventbrite IDs 1997432427159 and 1997432428162 both publish series URL ending 1997432305796, with distinct 19 and 26 October dates (including the correct BST/GMT offset). Evidence is `artefacts/data/sprint9-nct-parent-identity-candidate.json`. This is one qualified candidate, not an approved whole-branch mapping. The existing Alf King listing UUID a793340c-6833-4eb3-9e0b-3b8ed18c2877 currently retains only 21 December bounds. Extending identity enrolment to NCT and adopting existing rows requires its exact source-backed binding cohort and an occurrence-preserving writer; the accepted empty Ealing adoption cohort does not authorise unseen NCT mutations. No NCT binding or data repair has been applied.

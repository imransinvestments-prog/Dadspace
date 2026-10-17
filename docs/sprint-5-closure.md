# Sprint 5 review and closure — 17 October 2026

**Goal achieved: 24 committed, 24 accepted, zero remaining or carried over.** #122 (5), #123 (2), #124 (3), #127 (3), #126 (3), #130 (5), #176 (3) are closed. Timestamped acceptance events are retained in `artefacts/data/sprint5-burndown-ledger.json`; no ideal line or week-based velocity has been invented.

## Delivered and verified

- Fixed 50-venue /100 diagnostic-Activity /17-public-Deal packs retain exact IDs, provenance, eligibility/unknowns, selection queries and fingerprints. The owner explicitly accepted the diagnostic scope; final pilot qualification remains separate. The original 50-row News review was reused.
- Owner approved both remaining quality choices, all 17 Deals across all six scopes, the freshness/recovery targets and Activities discovery. Exact Deal selection and reviewed fields matched fresh production readback; no offer mutations were needed.
- Nineteen News geography corrections committed through two owner-approved, stale-safe atomic transactions; Monmouthshire remained a verified no-op. All 20 rows match the approved expected values with no unintended selected-field changes. Final targeting is Inverclyde for Port Glasgow, county-wide Cheshire for the multi-venue article, and Maldon/Essex for the Gazette article. Owner approvals supersede earlier conflicting notes; original labels are retained as history, not rewritten into invented rubric scores.
- The Cheshire filter now supports county-wide stories across its constituent districts while preserving district-only and nation guards. Ten actual public-view positive/negative cases pass. Production postcode normalization returned county Cheshire / district Cheshire East before application. Older News rows were verified in storage without being republished into the rolling public view.
- The historical dispatch gap is reconstructed, with the invisible GitHub cause explicitly unknown. Slot/source warnings and independent failure/zero-yield evidence are deployed. Targets are 60 minutes for dispatch, four hours for completion, 36 hours for source checks; recovery remains investigated and bounded, without automatic data changes. No seven-day scheduled acceptance is claimed here (#125 remains separate).
- Activities discovery exposed source, identity, renewal, age and location evidence gaps. Residual #180 (5), #181 (5), #182 (5), #183 (3) are provisional backlog stories with explicit exclusions for existing #40/#135/#146 work. They are not next-sprint commitments or a complete epic estimate. #101/#157/#158 and Community retain their previous deferrals/gates.

Release PR #179: `fc62f4f199a56cbbc6f3b3e09261cec070a0fe16`. Final News code PR #184: `5cc71d3458adce977fb500f7d29019b9596901d8`. Applicable hosted checks and Vercel production passed. Production owner review shows all 17 Deal passes; public Deals shows the same selection. Nineteen News corrections read back at 15:30 and 15:44 UTC. Forward/inverse SQL rehearsals retain an explicit rollback plan; a rollback never overwrites newer selected fields silently.

## Validation

158 Node tests, 11 Python locality tests, the News locality script and TypeScript pass. PostgreSQL checks cover atomic stale-batch rejection, forward/inverse rehearsal and duplicate URL preservation; the real worker's save protocol uses `resolution=ignore-duplicates`. Local webpack builds pass and hosted default builds pass. Local Turbopack process-spawn trouble was kept distinct from application/test failures. No paid model run, source/provider activation or permission change was required.

## Sprint review

**Went well:** scope stayed at 24 points; the large Activities uncertainty became bounded discovery and separate backlog work; completed reviews were reused; the owner could confirm all Deals once and the recorded checks remained traceable. Actual data readback and failure tests accompanied the release.

**Could improve:** the review desk initially required too many individual saves; status copy continued saying “proposed” after decisions were accepted; local/remote encoding and build-environment differences added verification overhead. Location names from a publisher/title proved insufficient without reading the actual source.

**Continue:** one consolidated decision pack, exact frozen cohorts, explicit unknowns, independent acceptance/release/data gates, reversible transactions and a review at every sprint closure. Prepare semantic place comparisons and bulk-review support during refinement. Refresh accepted-state copy as decisions land. Capture owner feedback on this retrospective when offered; do not attribute unprovided feedback to the owner.

No next sprint has been started. Next planning should re-sequence the new Activities foundation work before final feed acceptance, with a 25-point ceiling and no automatic stretch scope.

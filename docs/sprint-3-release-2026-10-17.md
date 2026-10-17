# Sprint 3 release — 17 October 2026

Owner reviewed the correction pack and approved application in chat. PR #172 merged as `1bb2ff1cf8b9ef8d9adea6fda120f3c6ee621e74`; Vercel production deployment succeeded.

- Protection migration applied: `20261017091914`, `protect_reviewed_venue_classification_country`. Repository filename is aligned to this actual migration-history version; SQL content is unchanged from the approved migration.
- Guarded SQL trial completed with ROLLBACK and exact expected totals, followed by an identical COMMIT run.
- Libraries: 3,440 public rows; 3,392 England, 48 Unknown (33 unmatched postcodes, 15 missing). All library publication flags retained.
- Little Garden Nursery: category nursery, public_visible false, access NULL. Its original approximate address and identity remain unchanged. Live detail URL returns 404; Hounslow Library remains public.
- 3,441 separate accepted audit/source records contain before-images, evidence and after-fingerprints. All 3,441 current row fingerprints matched after the transaction and import-protection test.
- Transactional simulated import attempted to restore nursery playground/publication and overwrite a reviewed England country with Wales. Category, publication and country protections passed; test transaction rolled back.
- Seven targeted local tests, compilation, full GitHub regression/checks and Vercel build passed before release. Production data readback passed after release. No reference-worker write run was dispatched.

Existing original operations protection remains intact. Geography evidence storage has RLS enabled with no anon/authenticated policies. No RLS grants, source activation or provider changes were introduced.

The proposal artifacts remain historical pre-application snapshots. The correction SQL deliberately refuses replay because accepted audits now exist. Recovery SQL defaults to rollback and checks after-fingerprints; no recovery was executed. The actual code release and data application are complete.

Tickets #162 and #100 earn 2 + 3 = 5 unique points once; #171 adds no points. Unknown library attribution is intentional; this does not certify current library operation or complete UK supply.

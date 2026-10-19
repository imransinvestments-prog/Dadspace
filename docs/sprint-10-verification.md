# Sprint 10 verification

## Released 19 October 2026

Owner approved review decisions and production release. PR #208 merged as `5b0a5258d8dbfc2e5e929b74d2c347d6166699b1`; Vercel production deployment passed. All five final-head checks were green at `ee13ab207c88e09bc945e687839c7001310173eb`, including real PostgreSQL 17. Live homepage/discovery routes and W3 lookup returned 200; anonymous geography access redirected to login with no reference exposed; the existing owner session rendered the full protected geography page. The release follow-up corrects approval/status labels only. Database migration/seed remains unapplied in production. Individual manual content/permission/persistence checks remain separately evidenced; approval is not fabricated test execution. The historical pre-release verification below remains intact.

Development branch `dev/geographic-coverage`; production untouched. Scope and acceptance: #202–#205. Owner browser/content acceptance is pending, so zero points are accepted and tickets remain open.

| Check | Evidence |
|---|---|
| Build | Local Next.js 16.3.7 webpack build passed. Existing Google Fonts fetch/build subprocesses required normal network/Windows permissions; no app code was changed to hide that dependency. |
| Types | TypeScript `--noEmit` passed. |
| Node regressions | Full suite: 186 passed, zero failed. Final affected tests after provenance and review fixes: seven passed. |
| Python regressions | Full suite: 273 run, 13 skipped, zero failures. Final geography suite: nine passed. |
| Isolated database | Actual schema/seed, repeated import, changed-content rejection, prior releases/termination, public-role denial, service-write denial, invalid graph/nation rollback and nonempty/empty inverse verified in PGlite. Persistent local catalogue rebuilt with final schema: 361 councils, 28 GB postcodes, production_connected=false. |
| Real PostgreSQL | Dedicated disposable PostgreSQL 17 hosted gate added; final run links/results recorded in #202 and the draft PR. PGlite results alone are not described as multi-connection PostgreSQL evidence. |
| Current feature baseline | 28/28 GB lookups passed; all 28 returned venues; ten Activity and six Event samples nonempty. Two NI cases blocked without geocode requests. Endpoint counts, pagination/completeness and quality limitations are retained. |
| Security/diff | Protected page owner/sign-in/denied/unavailable behaviour exercised through actual server component; no public DB grants, mutable client secrets, production writes or public runtime cutover added. All four reference tables have RLS, read-only service grants and release-preserving guards. |
| Lint | No lint script/configured linter in repository; no lint pass claimed. |
| Review | ECC Blueprint plan and implementation review performed; normalisation and stale national-evidence findings fixed and re-tested. |

First hosted head a91b138 passed Geography (including actual PostgreSQL 17), Operations, Guarded review, SEO and Vercel preview. The broad Deals job exposed an existing Matalan fixture clock mismatch at the real offer cutoff (#209). A test-only correction freezes both fixture clocks consistently and additionally asserts expiry at the exact cutoff; production offer dates and expiry rules are unchanged. Final-head hosted evidence is recorded on #202/#208 rather than treating the earlier red check as a pass.

Remaining owner checks: actual sign-in/session/location switching, denied-location/manual fallback, source/age/schedule/content quality, mobile/keyboard review and explicit decisions in `docs/sprint-10-geography-review.md`. News/Originals content review is manual. National-scale postcode import/performance and authority-wide sampling remain #207; NI commercial data basis remains unresolved. #206's scheduled observation starts only after an approved release and belongs to the subsequent sprint.

## ECC self-evaluation

| Axis | Score | Evidence / improvement |
|---|---:|---|
| Accuracy | 4 | Official code catalogue, retained provider attribution, actual endpoint results and isolated SQL checks; postal positions still approximate addresses and live content is not reviewed. |
| Completeness | 4 | Three implementation stories, follow-up/observation tickets, plan and review workspace delivered; NI geocodes and broader national import explicitly gated, with owner browser acceptance remaining. |
| Clarity | 4 | UI distinguishes bundled snapshot, local DB, point counts and unknown quality; the underlying UK's differing administrative structures still require the model notes. |
| Actionability | 4 | Bootstrap/check commands and preview test steps are concrete; actual owner sign-in and licence decision cannot be simulated as accepted. |
| Conciseness | 4 | One user workspace and decision pack; supporting technical plan/verification remain separate for engineering audit. |

Overall **4.0/5**. Highest-value next actions: owner tests the dev preview, resolves NI data basis before any use, and agrees national quality targets from observed gaps. This self-check does not replace acceptance or claim production readiness.

# Sprint 10 review — 19 October 2026

Goal: establish shared UK geography and reproducible feature checks before broader Activities expansion. Owner accepted the review pack and all decisions, then authorised production release. #208 released as `5b0a5258d8dbfc2e5e929b74d2c347d6166699b1`; #210 recorded accepted decisions/release wording as `eeb004c6d9ed1dfacfb6a335767a917a428659ff`. Both Vercel production deployments passed.

## Accepted delivery

#203 reference catalogue (5), #204 postcode pack (5), #205 coverage/review workspace (5): **15/15 bounded delivery points accepted**, zero tracker/parent roll-up points and no duplicated #209 test-repair credit. Exact official catalogue: 361 councils, 395 administrative areas; 28 GB postcode samples, 30 scenarios including two explicit NI licence blocks. The independently reproduced PGlite catalogue and real PostgreSQL 17 CI validate reference import, permissions and retained history. The workspace uses frozen snapshots and states that boundary openly; no production geography database import occurred.

Full local checks: 186 Node passed, 273 Python run/13 skipped, types/build passed. Five implementation and four release-record hosted checks passed, plus both previews. Production public Home/Places/Activities/Events returned 200 and W3 postcode lookup returned one location. Anonymous `/ops/geography` redirected to login without exposing the reference; the existing signed-in owner session rendered the protected catalogue, samples and licence gates. No source activation, provider purchase or public lookup cutover.

## What worked

One consolidated pack separated concrete decisions from engineering evidence and unknowns. The owner explicitly praised the pack and agreed its decisions. Official code reuse avoided a competing geography taxonomy. A fixed small sample exposed real geographic supply gaps without claiming complete national coverage. The plan review caught a postcode-normalisation defect and stale national-evidence rendering; both were fixed before release. One reference manifest and explicit hashes kept snapshots coherent across Windows/Linux.

## Improve

An existing Matalan fixture used one frozen adapter clock and a live validation clock. It failed as the real review cutoff passed during CI. #209 now freezes both and tests expiry exactly at the boundary; production dates were never extended. Future dated fixtures should declare all clocks before readiness checks. Release status wording initially remained a proposal after approval; #210 corrected it, so future review packs should separate historical proposals from current accepted status at the start.

## Carry-forward identified before start

#206 (2 provisional points) is post-release observation in the next eligible sprint, not earned by manual API checks. #207 (5 provisional, low confidence) is broader council sampling and national-scale licensed postcode import. NI data rights remain unresolved, numeric national content targets remain to be agreed, and individual browser/content review is not fabricated from general decision approval. The approved quarterly manual reference check has not become a new automation. Sprint 9 source/identity/NCT and existing observation windows are unchanged.

## Learning applied to Sprint 11

Reconcile existing accepted child work before sizing whole epics. Freeze exact factual cohorts and publication proposals; keep unavailable access and source evidence explicit. Distinguish code/preview, owner decisions, production mutation and scheduled observation. Capture all expected slots in Europe/London (including the 25 October DST change), preserve failed attempts and do not restart windows without an explained decision. Scope/estimates are relative effort, not inferred weekly velocity or a guarantee to close future Friday/seven-day gates immediately.

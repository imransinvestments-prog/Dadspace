# Sprint 4 — consolidated review

17 October 2026. Tracker: https://github.com/imransinvestments-prog/Dadspace/issues/174
Preview: https://dadspace-git-sprint-4-discovery-a-ac4b91-imransinvestments-6859.vercel.app/
Proposed release: https://github.com/imransinvestments-prog/Dadspace/pull/175

## Decisions to make together

1. **Release PR #175. Recommended: approve.** It adds reversible canonical redirects, closes withdrawn-event detail/sitemap gaps, reads public HTML afresh, distinguishes unavailable/partial supply from empty results, and removes unsupported structured-data claims. No new source/provider, schema migration or bulk content change.
2. **Aquarium pair. Recommended: merge London Aquarium into SEA LIFE Aquarium London.** Source `c1da600c-fae8-471e-8086-36d8ba82c6d2`; survivor `67ec8f30-7e2e-4c9f-a889-2bdeb5558e92`. Both use the same SEA LIFE operator website and County Hall address, SE1 7PB. Coordinates are about 147 m apart; identity is inferred from operator/address evidence, not proximity alone. Official confirmation: https://london-support.visitsealife.com/hc/en-us/articles/213042345-Where-is-SEA-LIFE-London-Aquarium-located . Exactly one source record becomes hidden and points to the survivor. Current preview counts: 0 linked listings, 0 venue_sources records. Source identity/source_url stays stored. Survivor facts stay unchanged. Re-read counts and generate a fresh stale-safe preview immediately before applying; no hard delete.
3. **Inwood pair. Recommended: retain both.** IDs `1f8152f2-d32d-40dd-9780-f912a2fa5d94` and `ddae32a9-056a-4d87-837c-7b3cb113c22f`. They share the generated label Inwood Avenue Playground, but https://www.openstreetmap.org/way/828533781 and https://www.openstreetmap.org/way/1206126846 show adjacent, distinct polygons about 57 m apart, created/adjusted in the same mapping changeset. The council also distinguishes main play and waterplay facilities: https://www.hounslow.gov.uk/downloads/file/11091/inwood-park-management-plan-2025 . Evidence does not identify which polygon has which ages/facility; no such labels will be invented. No rows change under this decision. Each currently has 0 linked listings and 0 venue_sources rows. Matching name/postcode will never trigger automatic merging.
4. **Reviewer write access. Recommended: enable only when ready to use it.** Operations reads/actions remain restricted to confirmed `imransinvestments@gmail.com`. Applying decisions additionally requires the separately verified account UUID reviewer permission. Release approval alone does not grant it. Enabling it requires permission to update the specific DADSPACE_REVIEWER_USER_IDS hosting setting for that account; no unrelated secrets need to be reported. Alternatively keep the desk read-only while approving a bounded engineering-applied aquarium transaction. Either route uses the audited transaction contract; no other records are approved by this packet.

## Completed engineering work

- #33: guarded decision controls released in PR #83 with owner approval; owner-only Operations restriction released. Reviewer writes remain disabled. Database migration `20261017102447` applied; anon/authenticated RPC execute denied. Zero live decision audits at latest readback.
- #89: explicit alias-chain resolver follows reviewed merged_into only, bounds chains and rejects cycles/private survivors. Source URLs redirect temporarily (307) so rollback can restore the old URL; renamed labels of the same identity retain canonical 308 behavior. Existing transactional importer/relationship/rollback tests cover merge preservation. No national deduplication.
- #137: withdrawn event details and core sitemap now filter withdrawn_at; Activity view and upcoming Event view already do so. Hidden venue list/detail/photo/RPC reads filter public_visible. Anonymous RLS-empty fallback removed from the server data client. Missing/failed/null/partial reads are unavailable, not zero supply. Home local-week responses are private/no-store. Public list/detail HTML is dynamic rather than cached for 10–15 minutes.
- #138: stable canonical IDs for Venue/Event/Activity graphs. Unknown/customer-only access no longer claims universal public access. Generic category falls back to Place. Event offers no longer guess a ticket price or InStock availability. Activity Thing omits unsupported location/category properties; visible facts remain on the page. Activity list uses a bounded CollectionPage/ItemList. Script escaping regression round-trips hostile names.

## Revocation and location contract

A committed visibility decision is reflected by the next completed fresh request to HTML, APIs, schema and sitemaps. Request-local React cache is not a shared cross-request record cache. Decision apply calls revalidatePath on the root layout. Existing browser views need refresh/revalidation; this release does not remotely erase an already-open tab or control search-engine caches. No hard wall-clock SLA is claimed for those external consumers. Location-specific APIs use private/no-store; canonical and sitemap URLs contain no personal coordinates. Preview metadata is noindex,nofollow and uses production canonical URLs.

Application rollback is a revert of PR #175; database history and aliases remain. No migration is required by PR #175. An actual aquarium merge can be reversed through the audited rollback only while the complete affected snapshot is unchanged. Revalidation follows either write. Do not drop history or restore over newer evidence.

## Evidence and acceptance limits

The live site was read, not seeded with fixtures. Production Home, Places, Activities, Events, News and Deals routes were inspected; canonical origin stayed https://www.dad-space.co.uk. Controlled hidden/revoked/newly-revoked states are exercised in isolated read-path tests and existing PostgreSQL transaction fixtures, never by altering unrelated live content. Existing #56/#57/#80 suites cover browser filtering, stale responses, pagination and source selection.

The fixture matrix covers missing configuration, query errors, thrown transport errors, genuine empty supply and later-page failures for relevant feed paths. News/Deals null results fail honestly; Home partial feed failures retain independent sections. Targeted tests include real route redirect behavior after merge/rollback and rejection of legacy operator access bypasses.

External Schema.org reports and current preview readback are saved with the sprint artifacts. Validation demonstrates schema vocabulary/shape and conservative claims; it does not establish Google indexing or event-rich-result eligibility. Missing optional facts remain omitted. Final checks/results are recorded in the PR and tracker.

No remaining ticket is closed by this document alone. After decisions: deploy approved code, enable only approved reviewer access, apply the one approved aquarium merge, confirm old/new URLs and public surfaces, verify imports preserve the resolved identity, then close applicable stories/tickets and record accepted points once. Retaining Inwood is a legitimate evidence-based outcome for that group.

## Final verification — 17 October

- 147 Node tests pass, including 13 Sprint 4 regressions; TypeScript and all PR CI checks pass at source commit a34ea893b9cd1af6019c94c26f401a165f76b0de. Vercel preview build succeeds.
- External Schema.org validator: zero errors and zero warnings on six representative list/detail pages. [Schema reports](../artefacts/documentation/sprint4-schema-validation.json).
- [Visible detail/structured ID comparison](../artefacts/documentation/sprint4-detail-readback.json): aquarium, NCT Lampton Baby Cafe and NCT Staines/Ashford/Egham Nearly New Sale names and canonical IDs match the rendered detail pages. Preview robots are noindex,nofollow.
- [Production route readback](../artefacts/documentation/sprint4-public-readback.json) records current production listing routes and canonical metadata before this proposed release. Home was separately inspected. This is a route smoke check, not certification of every content record.
- Existing hidden Little Garden Nursery detail returns 404 in the proposed preview; no venue entity is published there. Newly revoked states, alias rollback and hidden-photo refusal are controlled regressions; no live fixtures were introduced.
- Final owner decisions and approved follow-through remain pending. These results do not close #89 before the approved data outcome and post-release readback.

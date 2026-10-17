# Sprint 7 — consolidated decisions and delivery evidence

17 October 2026. [Sprint #187](https://github.com/imransinvestments-prog/Dadspace/issues/187), [preview PR #188](https://github.com/imransinvestments-prog/Dadspace/pull/188). The broader sprint release remains proposed.

## Decisions requested together

1. **One new offer:** approve the Matalan black school-jumper two-pack, **age 4 years**, exact variation **14894527**, item price **£7.20** against **merchant-advertised RRP £9**. Item saving £1.80 / 20%; no independent previous-price claim. Home delivery £3.99 gives £11.19 total for this item alone; standard click & collect £0.99 gives £8.19, subject to availability. Free-delivery thresholds and exclusions are in the offer evidence. This is a useful item-price reduction, not a claim that ordering this item alone saves money against an in-store purchase.
2. **One source route:** approve the bounded Matalan uniform pilot at https://www.matalan.co.uk/c/offers/school-uniform/ . First recipe checks only the exact product/size above, plus current category membership, delivery and promotion conditions. No general catalogue expansion, account or affiliate application. It stops conservatively at **19 October 00:00 BST (18 October 23:00 UTC)** because the published “19.10.26 at Midnight” wording is ambiguous. Any extension requires a fresh terms review; no automatic extension. Refresh exact evidence before any registration/activation and normal collector/public readback.
3. **Release:** approve the tested Deals workspace and bounded Matalan adapter in PR #188, once hosted checks pass. Keep existing owner-only permissions and disabled preview writes. No paid AI, automatic merchant applications or AWIN account changes are included.

Preview entry: https://dadspace-git-sprint-7-useful-deals-imransinvestments-6859.vercel.app/ops/deals?kind=trial . **One new content decision** is outstanding. The approved car-seat snapshot remains visible for context; the unchanged accepted 17-row Sprint 5 pack needs no repeat review. Matalan frozen fingerprint: `aac35fd5fc6c3f8db7c31c04a594e738b64a543d3efef515aa445d807cd0e311`.

## Decisions already approved and applied

Owner approved workspace usability and the Natural Baby Shower exact car-seat variant **55678800527739**, £169 vs merchant-advertised £289, plus its narrow source route. Focused PR #189 merged as 2821e6bd97d7e20bdc16bc2e6d6fe1e6b342aaf7. Source #42 was registered inactive and then activated through the production signed preview/confirmation flow. Registration audit 24352380-3a39-4c99-a1a2-33517495fe3f; activation audit 58be958b-5675-4696-976e-91afe5532543.

Normal rules-only collection [39070828554](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39070828554) fetched/verified one offer for source #42. Deal #1994 was read back live at £169/£289 and exact variant link on the [production Car Seats & Pushchairs page](https://www.dad-space.co.uk/deals?group=Car%20Seats%20%26%20Pushchairs). Last verification 17 October 22:27 BST. This manual run does not count as scheduled acceptance. No car-seat fitting recommendation is implied.

## Engineering decisions made on the owner's behalf

- Reuse the canonical taxonomy and public selector; no new taxonomy or affiliate-led ranking. Matalan maps to **School uniform sweaters #160**.
- Use an explicit 6 MB Matalan response bound (the product page is about 4.94 MB). Keep the existing 4.5 MB Shopify bound. Exact URL allowlist, four required public reads, no redirects, no merchant JavaScript execution or checkout access.
- Corroborate exact size/colour/stock/GBP price across the product's structured variant data and JSON-LD; use that variant's RRP only. Fail closed on missing or conflicting identity, price, currency, stock, terms, delivery or category membership. Re-fetch before verification.
- Summarise factual offer terms in our own words; no merchant description/image republication. Public robots inspection did not disallow the selected category/product paths; this does not confer an affiliate licence or blanket republication permission.
- Keep previews read-only. Source pause stops future collection; it does not immediately hide existing offers. Source decisions reuse signed identity, stale/concurrent checks, atomic audit and reversible readback. No taxonomy-writing API is added.
- Keep unaccepted observations separate from implementation. No whole feature points awarded yet.

## Priority coverage

| Priority | Outcome | Follow-up |
|---|---|---|
| Bicycles | Existing accepted Halfords supply; latest scheduled evidence verified two. | Retain route; review material changes only. |
| Car seats | One approved exact NBS variant, normal collector and production display verified. | Keep current stock/price checks. |
| Uniforms | One Matalan exact variant passed read-only normal classifier/value/verifier; no writes or model calls. Not yet owner-approved or published. | Owner decisions above, then fresh validation and audited activation/readback. #190. |
| Holidays | Canonical items 919/922 remain mapped gaps; no qualifying package route demonstrated. | Require dates, party size, mandatory charges and real comparison; breakfast discounts do not count as holidays. |
| Tuition | Explore Learning has pricing and eligibility-dependent financial support; no qualified collector route. | Require precise age, duration, location/mode, commitment and applicable discount; do not combine generic “from” prices with scholarship percentages. |

932 canonical rows, 294 active; all 308 active/priority rows mapped in the frozen coverage artefact. Stored status, source fetch success and actual public display remain separate. Bicycles and car seats establish two approved priority categories. Uniforms can become the third only after acceptance and live evidence. Missing holidays/tuition remain explicit follow-ups, not fabricated offers.

## AWIN dependency — still unresolved

Fresh [read-only audit 39069018906](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39069018906): six joined / six pending programmes, ten joined active UK promotions, normal collection zero verified AWIN offers. Relevant joined subset: Natural Baby Shower 64830, Bundle Baby 120946, Kokoso Baby 49101. Relevant pending subset: Kiddies Kingdom 2191, Medela 26969, Kit & Kin 47501, Mam Baby UK 75690, Chicco 99689. No applications or membership changes were made. Candidate network promotions are not accepted deals.

The owner-supplied and installed script `https://www.dwin2.com/pub.3111278.min.js` **still returns HTTP 404** on recheck. [AWIN's publisher installation guide](https://success.awin.com/articles/en_US/Knowledge/how-do-i-install-the-publisher-mastertag) confirms that URL format and describes activating a publisher plugin before testing. Its advertiser dwin1 script is a different product and must not be substituted. Actual account/plugin configuration has not been inspected or changed. Do not infer that a specific plugin is disabled solely from the 404.

Prepared account-side investigation: inspect Toolbox → Publisher MasterTag for publisher 3111278, record plugin/configuration state and use the existing account's supported test. If no active configuration explains the failure, provide the exact failing URL, HTTP 404 and the installed snippet to AWIN support. **No message sent and no plugin activated.** This dependency prevents claiming MasterTag delivery or closing #131; it does not block independent offer collection or workspace release. No repeated request for the same snippet is needed.

## Verification

Read-only Matalan trial: one fetched / one kept, canonical 160, exact variation and independent second merchant check, zero database writes / zero model calls. Six Matalan tests cover identity/currency/stock/price mismatches, malformed payloads, duplicate corroboration, unsafe URLs, redirects, response bounds, changed terms/delivery, network failures, cutoff and price changes. The test clock is frozen so an expired campaign does not break future regression runs.

Full Node suite **177 passed**; full Python discovery passed; TypeScript and webpack production build passed. No standalone lint command exists in package.json. Hosted checks and final deployed browser evidence are recorded in sprint-7-progress.md.

## Scheduled evidence and acceptance

#132 is outside the 21-point delivery commitment and still depends on #125's qualifying seven-day cross-feed window. Scheduled runs 39026086855 and 39067495389 on 17 October completed Deals successfully (pipeline 98/102, 538 fetched / 120 kept, zero health-write failures), but creation at 10:45:06Z / 20:37:24Z exceeded the expected 06:17Z / 18:17Z slots by more than the 60-minute allowance. “Kept” does not mean that many public offers. No passing window is declared; manual collection cannot replace scheduled evidence. #125 still requires at least three scheduled Activities collections. No Activities implementation is added.

21 committed / 0 whole-feature accepted / 21 remaining. #148 is a release/acceptance candidate; #131 and #190 still need the concrete Matalan decisions and live evidence, while #131 also retains MasterTag delivery. Close the iteration only after the agreed sprint review; do not close feature tickets merely to close an iteration.

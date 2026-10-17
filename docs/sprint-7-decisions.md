# Sprint 7 — evidence and decisions

17 October 2026. [Tracker #187](https://github.com/imransinvestments-prog/Dadspace/issues/187), [draft PR #188](https://github.com/imransinvestments-prog/Dadspace/pull/188). Implementation is not released or accepted.

## What has been established

- Frozen public selector replay: **17 displayed offers**, the same IDs and material offer evidence as the accepted Sprint 5 pack. No new review request for these unchanged rows. Routine last-seen refresh is not a new content decision.
- Full taxonomy snapshot: 932 items, 294 active; 308 active/priority rows mapped to observed item-level route history, configured candidate feeds or explicit qualification gaps.
- Existing supply does **not** satisfy three of the five priority categories. Bicycles have verified Halfords supply; car-seat and uniform feeds have zero verified offers in the latest collection. Holidays/tuition lack a qualified item-level route in this snapshot.
- Fresh read-only [AWIN audit](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39069018906): six joined, six pending programmes, ten joined active UK promotions. Baby discovery found 55 candidate programmes and 53 network promotions; these are not 53 qualifying deals.
- Natural Baby Shower (64830), Bundle Baby (120946) and Kokoso Baby (49101) are joined. Kiddies Kingdom (2191), Medela (26969), Kit & Kin (47501), Mam Baby UK (75690) and Chicco (99689) are pending. This list is the relevant baby subset, not the full six/six account list. No application or membership change was submitted.
- Direct browser check of the configured [publisher script](https://www.dwin2.com/pub.3111278.min.js) returned a 404 page. Successful MasterTag delivery is **not** accepted.

## Source qualification findings

| Priority | Evidence | Next bounded step |
|---|---|---|
| Bicycles | Existing Halfords collector verified two offers; accepted public sample contains bicycle supply. | Retain existing route and recheck only materially changed offers. |
| Car seats | Car-seat RSS fetched 30, verified zero. [Kiddies Kingdom catalogue](https://www.kiddies-kingdom.com/best-sales) advertises product-specific RRP comparisons, but catalogue/search evidence is not a qualified current product/variant/stock check. Programme remains pending. | Investigate a small direct merchant adapter or product-level evidence from an already joined merchant. Apply the existing merchant-advertised disclosure; do not represent RRP as historical selling price. No source activation prepared yet. |
| Uniforms | Uniform RSS fetched 30, verified zero. [Matalan uniform offers](https://www.matalan.co.uk/c/offers/school-uniform/?page=4) provides a candidate route; the category headline does not establish a qualifying discount on a specific size. [Tu campaign terms](https://tuclothing.sainsburys.co.uk/events/sale) surfaced an August offer that has ended. | Qualify exact current product/size/comparison evidence. Do not republish expired summer campaigns. |
| Holidays | Active canonical IDs 919/922 exist but no observed item-level supply. | Retain gap until dates, party size, mandatory charges and genuine comparison evidence are available. Breakfast discounts are not holiday-package coverage. |
| Tuition | [Explore Learning pricing](https://www.explorelearning.co.uk/product/maths-english-tuition) and [support conditions](https://www.explorelearning.co.uk/pricing/financial-support/) identify a candidate, with eligibility-specific conditions. No qualified collector route exists. | Do not combine a generic “from” fee with a scholarship percentage into an invented package price. Qualify exact duration, age, location/mode, commitment and applicable discount first. |

These are research findings, not proposals to publish these pages as offers. New merchant adapters and any activation need concrete evidence before the owner is asked to approve them.

## Decisions made during implementation

1. Reuse shared maintenance identity/signatures/atomic audit; expose source pause, activate and restore only. No taxonomy write API was needed to make current evidence inspectable.
2. Keep previews read-only. Pause affects future collection; it does not override the existing offer freshness/expiry rules.
3. Default the offer queue to the exact displayed set. Put long supporting evidence behind expandable details; retain paged access to all stored rows.
4. Preserve the accepted 17-row pack. Current incremental offer-review count is **one**, the separately frozen Natural Baby Shower trial below.
5. Leave all feature tickets open. No points awarded for this progress, no scope padding and no live data changes.

## Owner involvement still needed

- Review the workspace usability once hosted QA is complete; this is not source or release approval.
- MasterTag needs the current account-generated publisher script or account-side configuration check. The observed 404 cannot be fixed by marking installation as accepted. No plugin/account activation is authorised by this document.
- A bounded Natural Baby Shower car-seat route has now passed a local read-only trial and independent exact-variant recheck using the normal classifier/value/verifier functions. It yielded **one** candidate: Britax Römer Dualfix M Plus, Carbon Black, variant 55678800527739, £169 against merchant-advertised £289. Canonical item 75 is reused. Fingerprint: cd2b79e83f834099d0173cac0dadb6dfacd30757e5804552859f397baf221f71.
- Review that one candidate under “New offer review”. Recommended decision: approve its content and the narrow source route https://www.naturalbabyshower.co.uk/collections/sale-car-seats.atom under the existing merchant-advertised comparison policy, subject to a fresh check before any live collection. No source row has been created or activated. No affiliate tracking/commission is claimed.
- That candidate would add a second priority category alongside bicycles, **not satisfy all three required categories**. Uniforms, holidays and tuition remain gaps. The candidate is not a reason to close #131.
- The owner supplied the account installation snippet; it matches the configured 404 URL exactly. Do not ask for the same snippet again or substitute a guessed endpoint. Account/vendor troubleshooting remains open; no account/plugin setting has changed.

## Scheduled evidence (#132)

Two consecutive normal scheduled orchestrations ran on 17 October: [39026086855](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39026086855) and [39067495389](https://github.com/imransinvestments-prog/Dadspace/actions/runs/39067495389). Deals jobs completed successfully at 10:47:42Z and 20:40:09Z; pipeline records 98 and 102 record 538 fetched / 120 kept, live mode, no health-write failures. “Kept” is a collector counter, not 120 distinct public offers or proof of insertion.

The normal scheduler expects 07:17 and 19:17 Europe/London (06:17Z/18:17Z on this date). Those orchestration creation times, 10:45:06Z and 20:37:24Z, exceed the agreed 60-minute dispatch allowance. Timing associates slots provisionally; do not infer a passing window from green jobs. Source-level evidence, identity/terms/outage readback and #125's full seven-day cross-feed reconciliation remain required. No acceptance window is declared passed.

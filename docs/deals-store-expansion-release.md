# Dadspace MVP deals expansion — release notes for approval

7 October 2026 · Status: delivered on `codex/mvp-testing`, awaiting owner review.

The MVP feed now displays **18 offers across all eight high-level categories**, with **at least one priced product in each category**. This expands the previous nine-card, four-category pool. Five researched UK Shopify stores are registered and active in the existing sources table; each produced eligible offers through the normal worker.

## Added stores

| Store | Source ID | Latest fetch | Reverified variants | Public cards |
| --- | --- | --- | --- | --- |
| Babipur | 37 | OK; 23 variants | 19 | 3 |
| Cheeky Rascals | 38 | OK; 4 variants | 2 | 2 |
| Snuz | 39 | OK; 10 variants | 5 | 1 |
| BABYGO | 40 | OK; 14 variants | 4 | 1 |
| Trunki | 41 | OK; 3 variants | 2 | 2 |

Source validation covered public Shopify feed/product access, explicit GBP variant prices and stock, UK delivery evidence and robots rules. These are public catalogue sources; no new affiliate agreement is claimed. [Reviewed routes, mapping decisions and operating runbook](https://github.com/imransinvestments-prog/Dadspace/blob/codex/mvp-testing/docs/deals-store-expansion.md).

## Published category coverage

Observed on the deployed MVP page after live collection. Prices are item prices; applicable delivery costs and eligibility are disclosed on cards and must be checked at checkout.

| Category | Cards | Example published product and exact variant link | Current item price |
| --- | --- | --- | --- |
| Baby & Maternity Essentials | 3 | [Baby Brezza Food Maker Deluxe — Default Title](https://www.cheekyrascals.co.uk/products/baby-brezza-food-maker-deluxe?variant=43672382865558) | £179.99 |
| Car Seats & Pushchairs | 1 | [Harmony Insight Isofix R129 Booster Car Seat - Free C&C](https://www.hotukdeals.com/deals/harmony-insight-isofix-r129-booster-car-seat-4975858) | £35.00 |
| Days Out & Family Fun | 3 | [Peppa Pig Trunki — Default Title](https://www.trunki.co.uk/products/peppa-pig-trunki?variant=41359243411546) | £39.99 |
| Family Home & Safety | 1 | [BABYGO® Home Safety Kit — 2 Gates](https://babygo.uk/products/home-safety-kit-black?variant=57649417126270) | £90.00 |
| Kids' Clothes & Shoes | 5 | [Children's Nimbus Coat — 3 years](https://kite-clothing.co.uk/products/nimbus-coat-blue-c-54?variant=56457072705920) | £39.50 |
| Nursery, Beds & Sleep | 1 | [SnuzFino Cot Bed - White Natural — Cot Bed Only](https://www.snuz.co.uk/products/snuzfino-cot-bed-white-natural?variant=46937254363378) | £155.00 |
| School & Learning | 2 | [Frugi Navigator Backpack - Hotchpotch / Snow Scene — Default Title](https://www.babipur.co.uk/products/frugi-navigator-backpack-hotchpotch-snow-scene?variant=58276637770053) | £32.00 |
| Toys, Play & Outdoors | 2 | [Apollo Chaos Junior Mountain Bike - 20" Wheel](https://www.halfords.com/bikes/junior-bikes/apollo-chaos-junior-mountain-bike---20in-wheel-435318.html) | £144.00 |

Days Out also retains the Premier Inn children's breakfast benefit; the Trunki product satisfies the separate product-coverage request.

## Worker changes

- Reviewed store/title mappings resolve to the existing active Supabase taxonomy. Generic school/travel products require child evidence from the same product; inherently baby-specific items do not require clothing sizes.
- Newly reviewed stores select supported titles from one Atom page before fetching up to 12 products. Snuz/Trunki use public, same-host Shopify product JSON where their themes omit complete stock data; product ID and handle must match the GBP HTML page.
- The existing 120-verification cap is shared across sources and canonical items before additional size/colour variants. A transient HTTP 500 receives one bounded retry; persistent failures still stop that source's batch and do not renew freshness.
- Eight-category health reporting, exact variant identity, stock/current/comparison-price rechecks, byte limits, redirect blocking and safe failure remain in place. No new schema, service or paid AI was added.

All new Shopify cards say **Merchant-advertised sale** and show a **merchant comparison price**. These amounts are not independently verified previous selling prices; no verified percentage-saving claim is made. Existing value thresholds remain £10/10% or £1/20%. Unavailable variants, unsupported comparisons, weak offers, unreviewed types and ambiguous bundles remain excluded.

## Verification evidence

- Two successful manual live runs: [run 16](https://github.com/imransinvestments-prog/Dadspace/actions/runs/37659708992) and [run 17](https://github.com/imransinvestments-prog/Dadspace/actions/runs/37660431447). Each fetched **521 candidates**, persisted **120 reverified offers**, and used **0 AI calls / 0 tokens**. Public selection reduces equivalent products/variants to **18 cards, eight groups and ten providers**.
- All **32** stored variants from the five new stores retained the same IDs/ingestion identities on repeat. Database audit found **zero duplicate ingestion keys**.
- **67 Python regressions**, **16 shared selector tests**, TypeScript and Next.js build validation. The extra recovery regression verifies both successful retry and the hard retry limit. Deployment checks succeeded for the MVP implementation.
- Every rendered category filter has a correctly grouped priced product. Homepage deal titles/links match the first three selected Deals offers. Exact variant links, merchant-sale statements and delivery disclosures were checked.
- Review evidence: [MVP page](https://dadspace-git-codex-mvp-testing-imransinvestments-6859.vercel.app/deals), [ticket #48](https://github.com/imransinvestments-prog/Dadspace/issues/48), the runs' `deals-review` artifacts, and accompanying local category-check/published-review files.

## Limits and remaining acceptance

An initial live run hit a Babipur server error and published seven groups; the retry fix and both later complete runs restored School/Learning coverage. The existing pet exclusion rejects dog-themed Dougie luggage, while Peppa luggage and the child pillow publish. This false positive remains a review gap. Other catalogue types and additional stores remain outside the reviewed sample.

This is a current supply snapshot, not a permanent eight-category guarantee. Price/stock changes and outages can remove offers under the existing freshness rules. Uniform, holiday and tuition priority coverage, human quality labels, consecutive scheduled runs and seven-day observation remain open on the wider feed ticket.

**Code remains on `codex/mvp-testing`. Sources and deal data use the existing shared Supabase database and are not isolated to a preview database.** No production code merge or default-branch scheduler change was made. Pausing a source stops ingestion; existing cards remain subject to freshness/expiry. Immediate offer removal requires marking that source's offer records expired separately.

## Approval requested

Approve the MVP source expansion and the displayed offer pool described above, or identify adjustments before accepting it. Production code deployment and scheduler changes require a separate release decision. Ticket #48 remains open for the outstanding broader acceptance work.

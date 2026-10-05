# Deals quality delivery: DS-07 / DS-08

Draft implementation for [#36](https://github.com/imransinvestments-prog/Dadspace/issues/36) and [#37](https://github.com/imransinvestments-prog/Dadspace/issues/37). Products **and family days out** are in scope, as confirmed by the owner. Production launch and the final quality rubric remain review gates.

## Baseline, 5 October 2026

Read-only database audit: 35 offers, 27 live, eight expired. Only one live record has both a comparison price and discount; 26 have no recorded saving evidence. All three active sources are overlapping HotUKDeals tags: car seats, pushchairs and baby. This explains the concentration in baby products and merchants rather than broad family usefulness.

| Source | Current state | Decision |
| --- | --- | --- |
| HUKD car seat / pushchair / baby RSS | Active; all three returned HTTP 403 from this local audit | Retain as discovery sources, but require a readable offer page before publishing. Do not infer expiry from 403 or missing entries. Confirm access in the Actions environment. |
| HUKD pram / cot | Inactive; overlaps current narrow tags | Keep inactive until a source review shows additional useful coverage. |
| HUKD sitewide new / hot | Inactive; broader coverage with substantial irrelevant noise | Trial in dry run and label accepted **and rejected** examples before enabling. |
| Awin | Inactive; requires publisher token, advertiser memberships and GB offers | Adapter corrected against current provider documentation. Prioritise relevant family merchants and attractions; credentials and feed coverage must be validated before enabling. |
| FMTC | Inactive; requires subscription/token and merchant configuration | Adapter corrected for pagination, restrictions, status and expiry. Validate subscribed UK family retailers and attractions before enabling. |
| Pepper REST | Inactive; endpoint/access contract unverified | Keep inactive. This implementation does not claim its availability contract is verified. |

Momcozy's conditional £54 wishlist price could previously be selected instead of the source's leading £63.99 price. FMTC titles containing “was … now …” could select the old price as current. Both have regression coverage.

## Proposed rubric implemented

Audience relevance and value are separate gates. Products must pass the existing family relevance classifier with quoted evidence and score at least three. Explicit kids-eat/go-free and 2-for-1 family ticket offers with participation conditions are recognised as family days out, without relying on an LLM to accept them.

Product savings need a current price and an explicit selling-price comparison. RRP alone and a bare “50% off” do not qualify. A useful supported saving is at least **£10 and 10%**, or **£1 and 20%**. These are conservative proposed thresholds awaiting the content review under DS-02; they are not a measured audience preference. Comparison prices remain **source claims**, labelled that way on cards.

Family benefits need clear conditions in the source text. Missing terms, unknown regular prices and weak savings go to the review output rather than public top picks. Delivery charges and restrictions are retained in full description text when supplied; cards tell readers to check the final total. A future structured total-cost comparison would improve this further.

Source checks use explicit active status and start/end dates for Awin/FMTC. HUKD RSS candidates require the expected offer title on a reachable HTTPS offer page; 404/410 and structured unavailable status remove eligibility. Authentication challenges, redirects, rate limits and network failures are inconclusive. The check fetches only supported HUKD hosts, follows no redirects and caps response bytes. These checks establish **source availability**, not a tested merchant checkout or guaranteed stock.

Both public surfaces use `selectDeals`: source-checked quality version, family evidence, supported value, unexpired known dates and last seen within 72 hours. The 72-hour window accommodates the current two-day collector cadence; stale records are hidden rather than marked expired. Ranking combines relevance, absolute/percentage value and freshness with merchant/category repetition penalties. Affiliate status and commission do not affect ranking.

Redemption URLs retain codes, variants and tracking. RSS identity removes only common marketing attribution and sorts query parameters; API identity uses the provider offer ID, so tracking URL changes do not create another offer. Legacy rows are deliberately ineligible until recollected and checked. Existing comparison values are not backfilled or relabelled as verified.

## Review and release procedure

1. Run `deals_collect.yml` with `dry_run: true` after verifying source access and configuration. Review kept **and rejected** CSVs, including description/terms and expiry. Dry runs now write neither offers nor pipeline logs.
2. Agree the rubric and label representative examples for baby gear, essentials, older children, family tickets and meals. Include generic products, unsupported claims, conditional prices, RRP and weak savings as negative examples. The checked-in examples are engineering regression tests, **not owner/content-reviewer acceptance labels**.
3. Test collection twice in a preview/staging database. Confirm stable provider identities, unchanged redemption URLs, preserved known expiry when a source omits it, no revocation from source/model outages, and removal of known unavailable/changed weak offers. Rejected source/model checks cannot refresh `last_seen`.
4. Run the app against that database, export its rows as a JSON array, then `node scripts/export-deals-review.mjs snapshot.json review/`. This uses the exact public ranking to generate `published-review.csv` (up to 100 offers) and `top-20-review.csv`.
5. A content reviewer labels every `human_*` column `yes` or `no`, checks links, eligibility, delivery, known expiry and savings basis. Run `python scripts/check-deals-review.py review/published-review.csv review/top-20-review.csv`. Empty or incomplete reviews fail. Known expired offers or unsupported savings claims fail regardless of overall score. At least 90% of published offers and 18/20 top offers must pass; when fewer are available, report the exact smaller denominator and obtain the Phase 0 agreement rather than claiming a 100-offer audit.
6. Complete the Linux build/preview checks and public journeys for populated, empty and failed states, then approve rollout. Recollect checked offers before switching the UI; otherwise the new filter will correctly show an empty feed. No production DB changes or source activation were performed during this implementation.

## Verification and remaining gates

Automated checks cover structured/conditional prices, ambiguous prices, RRP, supported absolute savings, family benefits, redemption identity, date/status rejection, source pagination and partial failure, source-page verification, outage-safe expiry, dry-run writes, shared selection, diversity, empty states and invalid links. TypeScript checking passes locally. The Windows sandbox blocks Next's native path canonicalisation during `next build`; `deals-quality.yml` provides the Linux regression/typecheck/build check on PRs.

Remaining acceptance: source access/credentials, reviewer agreement and labels, staged repeat-ingestion audit, populated preview and final release targets. Keep both tickets open until those gates have evidence. This change improves eligibility and pipeline correctness; it does not establish that the currently configured sources provide a sufficiently broad or useful published feed.

Provider mappings checked against [Awin Retrieve Offers](https://help.awin.com/apidocs/promotions) and [FMTC Deals 4.2.0](https://docs.fmtc.co/kb/deals-4-2-0). Supabase reads use the existing schema and server-only client; no schema migration or RLS change is required.


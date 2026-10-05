# Parent-value deals feed — issue #48

Work branch: `codex/mvp-testing`. Publish this branch only after MVP approval.

## Costs and limits

The normal collector is rules-only. `ENABLE_PAID_AI=false` is explicit in the workflow and no AI keys are provided to its steps. Unmapped items go into the decision report; they do not trigger model calls. Existing optional model code is disabled by default, including when a key exists. No new paid subscription, scraping browser, vector database or proxy service is needed. Awin/FMTC remain inactive; do not enable a subscription to fill a quota.

Use the existing GitHub Actions runner and Supabase database. These have account-wide usage limits; this change does not promise unlimited free hosting. Keep the two-day collection cadence initially and measure run time before increasing it. The public freshness window is 72 hours. Concurrency serializes collectors across branches because the database is shared. API pagination is capped at 20 pages; taxonomy reads page 500 records at a time and fail beyond 10,000 rather than silently truncating. Each run permits 120 offer checks. Halfords discovery uses one listing page, at most 50 candidates, a 4.5 MB page limit and 15-second response timeouts. Only verified offers renew `last_seen`.

GitHub scheduled workflows use the repository default branch. A preview push alone does not change the scheduled collector. During MVP testing, dispatch **Dadspace deals** with branch `codex/mvp-testing`, `dry_run=false`, `self_test=false`. A scheduler-only change to run this reviewed branch requires the owner's exception to the branch-only instruction. After launch, the existing default-branch daily-workers workflow calls this collector with no branch override.

## Canonical taxonomy and decisions

`public.parent_discount_items` is the source of truth. Deals reference its stable `id` through `deals.item_id`. Public grouping reads the linked active taxonomy row; an inactive or unmapped item cannot appear. All active rows have a matching-rule or a reported supply/classifier gap in the exported taxonomy CSV. No Excel or parallel product taxonomy is introduced.

The 5 October audit contained 932 rows, 287 active. Controlled changes activate seven owner-requested scopes: private, group and online tutoring; school tuition; family package holidays; ski holidays; and kids meals at restaurants. Tutoring maps to School & Learning, holidays and meals to Days Out & Family Fun. Holidays are marked `big`; services require explicit child evidence. This does not make free introductory consultations a discount. Existing value thresholds remain unchanged. Holidays additionally require dated travel, adult/child party size and fee details; tuition requires subject, age, mode, session duration and commitment terms. Missing detail or genuine price evidence remains a rejection.

Incorrect standalone nappy aliases were removed from liners, cream, bins and refills. Canonical wipe IDs 8 and 9 share an equivalence identity, keeping one best wipe offer across brands and packs. Uniform aliases now include school shirts/dresses/trousers; bicycle aliases include bike/training bike but require child evidence. Other exclusions stay in force. Pet, cleaning and second-hand exclusions are hard rules; adult terms remain conditional so an adult-meal requirement does not suppress a genuine family offer.

DB changes are additive migrations. The pre-change audit and controlled data-change SQL are retained as delivery evidence. Restore those audited taxonomy values if rollback is needed; disable individual new sources by URL, without deleting offer history. Frontend rollback may leave additive fields in place.

The reviewed data changes are recorded in `docs/deals-reviewed-data.sql` for replay against an existing canonical taxonomy after the additive migrations. They were already applied to the shared Dadspace database; the replay does not create a competing taxonomy.

## Coverage and source matrix

Every HUKD tag is one provider, not an independent source company. All listed active RSS routes returned 30 parseable entries during the 5 October trial. Source-listed claims remain distinct from checkout verification. No commission field affects ranking.

| Canonical group | Current discovery routes | Coverage limit / follow-up |
| --- | --- | --- |
| Baby & Maternity Essentials | HUKD baby | Many unsupported comparisons; keep one eligible wipe, never fill slots with repeats |
| Car Seats & Pushchairs | HUKD car-seat, pushchair | Verified booster-seat supply; continue sourcing models and delivery terms |
| Days Out & Family Fun | Premier Inn direct breakfast page | Two under-16 breakfasts with a full adult breakfast; prices/availability vary. Holiday feeds `holidays`, `package-holidays`, `family-holidays` returned 404; licensed travel or validated provider routes still needed |
| Family Home & Safety | HUKD baby / broad child-product discovery | No dedicated validated safety feed; explicit supply gap |
| Kids' Clothes & Shoes | HUKD school-uniform, kids-clothes | School uniforms are a priority. Posts listing multiple products cannot mix one product's price with another's comparison |
| Nursery, Beds & Sleep | HUKD baby-monitor, baby | Monitor route works; cot and cot-bed tags were unusable/404 in trials; supply gap |
| School & Learning | HUKD board-game plus reviewed service taxonomy | Tutoring/tuition tags returned 404. Explore Learning trial and MyTutor pricing pages reviewed: no comparable paid tuition discount evidenced, so no offer published |
| Toys, Play & Outdoors | HUKD toy, board-game, kids-bike; Halfords direct children-bike listing | Retailer JSON supplies current and regular price comparisons. Each candidate is checked again on its product page for matching price and stock before publishing |

Priority follow-ups: holidays need specific dates/party/mandatory-fee packages, not generic 'from' prices. Tuition needs comparable sessions and ongoing costs, not a free sales consultation. Uniforms, car seats and bicycles have validated working discovery routes; the final run report records accepted and rejected examples rather than promising a constant discount supply.

Additional trials: HUKD `bicycles`, `toys`, `school-shoes` returned 404 (correct working variants differ). PizzaExpress terms were readable, but its current offers page did not advertise the kids-eat-free campaign, so the reviewed recipe fails closed and is not active. Beefeater redirected to a generic Premier Inn page and cannot be counted as independent supply. Dunelm's cafe page advertises a spend-based benefit, but has not passed the current eligibility recipe and stays out. Halfords' weaker £8/10% Sweetie offer fails the existing value thresholds. Awin, FMTC and Pepper remain inactive/unvalidated for this release.

An Ocado school-dress product page was found through public search, but the actual collector request returned HTTP 403. A search result alone cannot renew freshness or establish availability, so this is a source-access gap, not an accepted offer. No paid proxy or protection bypass was introduced.

## Initial live evidence — 5 October 2026

Testing commit `3e7f4c58a0fde50d45abb0972ca5e0c50fcea3a0` passed 41 Python tests, 15 public-selector tests, TypeScript checks and the Vercel preview build. Two manually dispatched live collections succeeded:

| Run | Candidates | Verified offers | Collector time | AI calls / tokens |
| --- | --- | --- | --- | --- |
| [11](https://github.com/imransinvestments-prog/Dadspace/actions/runs/37381540276) | 274 | 4 | 37.4 seconds | 0 / 0 |
| [12](https://github.com/imransinvestments-prog/Dadspace/actions/runs/37382206326) | 274 | 4 | 32.7 seconds | 0 / 0 |

All eleven active routes fetched successfully. The repeat run refreshed the same deal IDs 4, 103, 104 and 105; the database contained zero duplicate ingestion identities. The public pool contains one Argos booster seat, one Premier Inn breakfast benefit, and two distinct bike types from Halfords. This is three independent discovery providers, three canonical groups, two priority groups with offers, and 50% Halfords concentration. It falls short of the four-group and three-priority-group targets; no human approval or seven-day reliability result is claimed.

The populated preview showed four cards, truthful benefit/price conditions, all eight canonical group filters, two bike cards in the populated outdoors category, and an honest empty clothes category. Homepage cards use the same pool. Full published-pool review remains blank for the owner/content reviewer. Artifacts on both runs include published JSON, review CSVs, taxonomy coverage, source counts and feed-health reports. These two manual runs are repeat-ingestion evidence, **not** the required two scheduled collections.

## Run and recovery

1. Run regression checks and the workflow self-test on the testing branch.
2. Dispatch a dry run. Download `deals-review-<run id>` and inspect rejected cases as well as accepted ones.
3. Dispatch live only from the reviewed branch. Known expired/unavailable and weak offers move out of the feed; network failures do not infer expiry.
4. Inspect Actions status, the job summary, `run-health.json`, `feed-health.json`, all decisions and `taxonomy-coverage.csv`. A fetch success is separate from `last_verified_at` and per-source verified counts. A failed source remains active for retry and never refreshes offer timestamps. Degraded runs fail visibly after saving any independently verified good offers.
5. Check both preview `/deals` and `/api/home/deals`. The same selector, taxonomy grouping and card render are used across the homepage and Deals page. Category filters show honest empty states. Full conditions remain accessible on each offer.

`scripts/deals-health.py` reads source health and seven days of `pipeline_runs`, invokes the exact public selector, and reports stale hidden rows, provider/merchant/group/item counts, missed refreshes (54 hours), zero verified supply and diversity shortfalls. Reports use taxonomy IDs. Human published/top-20 CSV labels start blank: automated eligibility is not human approval.

Do not close #48 until two consecutive scheduled collections, the seven-day observation, the complete published-pool review (including an agreed denominator if fewer than 20), and populated preview checks are recorded. Aim for four groups and <=50% merchant concentration when useful supply permits; retain quality rather than manufacturing offers to meet quotas.

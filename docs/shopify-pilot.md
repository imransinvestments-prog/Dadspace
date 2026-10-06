# Shopify two-merchant MVP pilot

The worker reuses its existing `direct` source type, canonical Supabase taxonomy,
verification, equivalent-item selection and health reporting. No new database
schema, application service, paid search provider or frontend feed is required.

## Reviewed shortlist — 6 October 2026

| Merchant | Discovery keywords | Public collection feed | UK delivery evidence |
| --- | --- | --- | --- |
| Kite Clothing | baby, children, clothing, hat, leggings | https://kite-clothing.co.uk/collections/baby-children-outlet.atom | https://kite-clothing.co.uk/pages/delivery |
| MORI | baby, children, sleepsuit, pyjamas, sleeping bag | https://babymori.com/collections/sale.atom | https://babymori.com/pages/delivery |

Both shops serve UK customers and expose Shopify public HTML and Atom feeds.
Their robots files allow the selected feed/product routes as audited on this date.
The pilot reads those public documents; it does not use undocumented catalogue
JSON endpoints, Admin APIs, browser execution or checkout. This establishes a
public collection route, not an affiliate agreement or merchant endorsement.
MORI and KIDLY must not be counted as independent merchants: KIDLY is part of MORI.

## Collection and limits

`deals_shopify.py` allows only these two feeds and same-host product paths.
Each run samples at most two Atom pages and 12 unique products per merchant;
it reports this bound explicitly, not full catalogue coverage. Responses are
limited to 4.5 MB; redirects are disabled; transient failures get one bounded
retry. Product requests are spaced. Repeated pages, malformed data, inaccessible
products and missing GBP/variant evidence fail closed without partial publication.
Products with more than 250 variants are reported incomplete. Prices are taken
from the exact variant in embedded product JSON; JavaScript is never executed.
Sold-out/subscription-only variants are rejected. Identity includes merchant,
product and variant, and links preserve the selected variant. Existing canonical
taxonomy and equivalent-item ranking prevent variant proliferation on the site.

## Value evidence and publication

Catalogue `compare_at_price` is retained in adapter review data, never converted
automatically into a regular selling price. Unsupported values are rejected by
the normal worker, including misleading benefit language in catalogue descriptions.
The versioned `shopify-value-reviews.json` starts empty. To qualify a variant, a
reviewer must record its identity, reviewer, evidence URL, current/regular prices,
exact live-page phrase establishing the regular price, and timezone-aware
`valid_until`. Do not use an RRP or crossed-out price as sufficient evidence.
The adapter checks the current price and phrase before classification; the verifier
rechecks stock, price and comparison evidence before publication. Expired reviews
and changed evidence cannot publish. Delivery conditions are disclosed in each
candidate; re-review them when enabling a merchant. Known offer expiry is not
invented: `valid_until` is the review/publication deadline.

## Run and registration

Run the **Shopify two-merchant pilot** workflow on `codex/mvp-testing`. Default:
the normal worker reads canonical taxonomy/exclusions and writes only local review
artifacts, with paid AI disabled. Synthetic source IDs identify the two pilot
merchants in this dry run. No deal, source-health or database run-log writes occur.
Review accepted/rejected CSVs and run-health JSON in `shopify-pilot-review`.

Optional `register_inactive=true` registers missing sources as inactive using the
existing registry and checks readback. Existing registrations are never enabled
or overwritten. This option has no live-deal ingestion or activation side effect.
Do not enable sources until their supply/value evidence and delivery terms are
reviewed. Registration and site publication are separate milestones.

After eligible evidence is reviewed, enable only the approved registered source,
run the normal collector on the MVP branch, and inspect both homepage and Deals
filters, variant URLs, prices, delivery conditions and shared item deduplication.
Disable that source to stop ingestion; already-published records remain subject
to normal freshness/expiry rules. An outage must not renew freshness or infer expiry.

## Outstanding acceptance

The two merchants' catalogue comparison prices alone do not meet the valuable-deal
rubric. Live dry-run outcomes and registration evidence are recorded in issue #48.
No promise of additional public cards is made until eligible evidence is supplied.
Human review, useful live publication, two scheduled runs and seven-day observation
remain acceptance work. Automated search and historical price tracking are deferred.

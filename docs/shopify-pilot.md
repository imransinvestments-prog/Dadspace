# Reviewed Shopify MVP sources

The original two-merchant scope below is expanded by the
[7 October store review](deals-store-expansion.md). Use the **Reviewed Shopify
sources pilot** workflow. Newly reviewed stores sample one Atom page, selecting
only reviewed product titles before fetching up to 12 products. Snuz and Trunki
also use their same-host public `/products/<handle>.js` storefront endpoint where
their themes omit complete stock data. The endpoint's handle and product ID must
match metadata on the GBP product page. No Admin API or credentials are used.
Existing Kite/MORI bounds and publication rules continue to apply.

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
Sold-out/subscription-only variants are rejected.
Explicit variant ages up to 24 months or 12 years supply child evidence in titles;
adult/teen sizes and generic S/M/L labels do not. Missing canonical aliases remain
review gaps; the adapter does not create a competing taxonomy.
Identity includes merchant, product and variant, and links preserve the selected variant. Existing canonical
taxonomy and equivalent-item ranking prevent variant proliferation on the site.

## Value evidence and publication

On 6 October the owner approved clearly labelled **merchant-advertised sale offers**.
Available GBP variants in the reviewed sale collections can qualify using the exact
variant's current price and a numeric, higher merchant `compare_at_price`. Existing
minimum-value thresholds still apply (£10/10% or £1/20%). This is merchant evidence,
not proof of a previous selling price or independent savings verification.
Cards show **Merchant-advertised sale**, the merchant comparison price and an
explicit statement that previous selling price/savings have not been independently
verified. No verified-savings badge or percentage-off claim is displayed for these
offers. The existing database fields carry prices; the verifier's provenance marker
`quality-v1:source-page:merchant-advertised:rules` carries the disclosure distinction.
Both homepage and Deals page use the same card and eligibility logic; no schema
change is required.

Complete embedded product JSON supplies variant stock/prices and merchant product
type. Placeholder descriptions (such as `1`) are replaced by richer same-product
JSON or matching product JSON-LD. Reviewed types resolve to existing active canonical
taxonomy labels and IDs (hats 136, trousers 118, mittens 138, pajamas 126, winter
coats 130 and raincoats 131, among the supported types). Waterproof evidence takes
precedence over generic warmth when distinguishing outerwear. Unknown types remain
unmapped; no new taxonomy or broad ambiguous keyword aliases are introduced.
Mappings require explicit child evidence. Adult/unsupported age variants remain
excluded even when a richer description mentions children.

The verifier independently reloads each product page once per collection run and
checks every eligible variant against that snapshot: stock, GBP, price, comparison
and evidence category. Changed/removed comparisons or unavailable variants cannot
publish. This cache is local to a verification run, not reused from discovery or
between runs. Existing freshness, item-equivalence and diversity gates still apply.
Delivery conditions are disclosed in each card; check final checkout costs.

The optional versioned `shopify-value-reviews.json` remains available for stronger,
time-bounded regular-price evidence. It requires reviewer, evidence URL, exact
live-page regular-price phrase and a timezone-aware validity deadline. A withdrawn
review cannot silently retain the stronger evidence category; merchant-advertised
offers may instead qualify on a subsequent collection with the appropriate label.

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

The owner-approved merchant-advertised evidence policy supersedes the initial
blanket rejection of Shopify compare-at prices. Live collection/publication evidence
and remaining mappings are recorded in issue #48. The two sources are active in
the shared registry, with the adapter and site changes held on `codex/mvp-testing`.
Human quality review, scheduled operation and seven-day observation remain open.
Automated search and historical price tracking are deferred.

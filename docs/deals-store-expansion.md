# Reviewed UK store expansion — 7 October 2026

Code is held on `codex/mvp-testing`. Source and offer records use the existing
shared Supabase database; activating sources is not isolated to a preview database.
No schema, paid service, AI classifier or competing taxonomy was introduced.

## Selected public sources

| Store | Source ID | Feed | Reviewed canonical products | Delivery evidence |
| --- | --- | --- | --- | --- |
| Babipur | 37 | https://www.babipur.co.uk/collections/all-sale-at-babipur.atom | GroVia all-in-one nappies (2); Frugi backpacks (166), lunch bags (167), raincoats (131) | https://www.babipur.co.uk/policies/shipping-policy |
| Cheeky Rascals | 38 | https://www.cheekyrascals.co.uk/collections/sale.atom | Baby Brezza bottle warmer (24), food maker (47); reviewed Fred stairgate (90), Love To Dream swaddles (63) | https://www.cheekyrascals.co.uk/pages/our-delivery-promise |
| Snuz | 39 | https://www.snuz.co.uk/collections/outlet.atom | Cot beds (929), changing tables (71) | https://www.snuz.co.uk/pages/delivery |
| BABYGO | 40 | https://babygo.uk/collections/baby-proofing.atom | Baby gates (90), babyproofing kits (96), cabinet locks (92), corner guards (93) | https://babygo.uk/pages/delivery-information |
| Trunki | Registration pending final pilot | https://www.trunki.co.uk/collections/the-explorers-sale.atom | Dougie/Peppa children's luggage (561), Una neck pillow (567) | https://www.trunki.co.uk/pages/delivery-cancellations |

Primary merchant collection/product pages establish the shortlist; these are
public catalogue sources, not newly agreed affiliate partnerships. Keyword discovery
was reviewed manually; there is no automated broad internet scraper. Each selected
feed and delivery page returned HTTP 200 on this date; robots.txt permitted the
selected public feed/product routes. Snuz/Trunki public JSON routes are also
permitted. UK eligibility, current GBP prices and available exact variants are
checked again through normal collection and verification.

## Implementation and review limits

New stores use explicit title patterns reviewed against existing active taxonomy
labels. Unknown products, replacement parts, refurbished/pre-loved stock and
ambiguous bundles are not fetched or forced into generic mappings. A marketed
home safety kit maps to the existing babyproofing-kit item; its actual variant
contents remain visible in the description and link. Generic school/travel products
require child evidence from the same product's description or title. Inherently
baby-specific canonical items do not require clothing-size evidence.

New stores use a one-page Atom sample, up to 12 reviewed products and 250 variants
per product. This avoids claiming that non-paginating feeds expose full catalogues.
Kite/MORI retain their existing two-page bounds. Requests remain allowlisted,
same-host, spaced, byte-limited, redirect-blocked, and have one transient retry.
Missing product/stock/currency evidence fails closed. Public JSON fallback additionally
corroborates exact handle and product ID against the HTML page.

The verifier retains a 120-check cap but shares it across sources and canonical
items before checking further size/colour variants. Verification snapshots are
run-local. Changed current/comparison prices and sold-out variants cannot refresh.
Existing freshness, item equivalence and diversity selection still apply. Feed
health now reports missing coverage against all eight canonical groups.

Catalogue comparisons remain **merchant-advertised**, not independently verified
historical savings. Existing £10/10% or £1/20% thresholds remain enabled. Cards
display the disclosure and delivery terms. No affiliate commission affects ranking.

## Evidence and rejected candidates

[Successful six-store pilot](https://github.com/imransinvestments-prog/Dadspace/actions/runs/37658134855)
returned 118 reverified variants with no AI calls/tokens, including Nursery 5,
Baby 4, Home/Safety 4 and School 3. It registered sources 37–40 inactive; activation
followed successful review and database readback. The pilot is a dry run, not site
publication evidence. Final normal-run/public-page evidence belongs in the release notes.

The first trial exposed Cheeky's repeated page and Snuz's missing embedded stock
data. Those failures were resolved without weakening value or stock checks.
BABYGO's gate currently lacks a comparison price, while its qualifying safety kit
has one. Weak-discount and unmapped products remain rejected.

Bigjigs was deferred because the initial embedded-data parser could not confirm
variants; Yes Bebe's selected feed was empty. CuddleCo could not be validated
within the bounded access checks. The School Outfit shortlist did not establish
suitable child-sized/value supply. These stores were not activated.

## Operation and rollback

1. Dispatch **Reviewed Shopify sources pilot** on `codex/mvp-testing`; inspect
   accepted/rejected CSVs and source health in `shopify-pilot-review`. Optional
   registration creates missing sources inactive and leaves existing activation unchanged.
2. Activate only reviewed successful sources. Dispatch **Dadspace deals** on
   `codex/mvp-testing`, `checkout_ref=codex/mvp-testing`, `dry_run=false`.
3. Inspect normal-run review, `published.json`, eight-group coverage and source
   health. Check the Deals filters, homepage shared selection, exact links and
   visible merchant-sale/delivery disclosures.
4. To pause a source, set only its exact registered `active` flag false. Existing
   offers age out under the normal 72-hour freshness rule; deactivation is not
   immediate offer removal. For immediate rollback, separately mark that source's
   offer records inactive using the existing supported status workflow.

Default-branch scheduling remains a separate release decision. Manual verification
does not satisfy two consecutive scheduled runs or the seven-day observation and
human-quality acceptance in issue #48.

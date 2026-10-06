# AWIN baby feed API trial — 6 October 2026

[Successful read-only run](https://github.com/imransinvestments-prog/Dadspace/actions/runs/37490319819). Artifact: `awin-baby-audit` / `awin-baby-audit.json`. No database writes or programme applications.

The API returned 3,380 UK programmes: three joined and six pending. Keyword discovery matched 54 programme names/descriptions mentioning baby, infant, newborn, nappies, pushchairs, car seats or maternity. This is a candidate shortlist, not a human-approved merchant list: broad retailers can also match.

The joined active UK offer query returned zero offers. Querying `membership=all`, `regionCodes=[GB]`, `status=active`, `type=all`, and discovered `advertiserIds` returned 47 offers. These are network-listed promotions, not 47 verified valuable baby deals or display banner creatives. Broad store campaigns and 'up to' claims must pass the existing relevance/value gates before publication.

Representative source-listed results: Kiddies Kingdom 10% off full-price items; Medela free maternity bra with a Freestyle Mini pump; Chicco autumn savings up to £50; Bundle Baby Bugaboo/travel-system campaigns; Natural Baby Shower Green October. All shown representative advertisers were unjoined. Do not publish missing voucher codes, invent product-level savings or count generic promotional copy as a deal.

Kokoso Baby (49101) is joined. Kit & Kin (47501), Natural Baby Shower (64830), Mam Baby UK (75690), Bundle Baby (120946) and MyPura.com (128441) are pending. Other candidates include Kiddies Kingdom (2191), Mamas & Papas (6526), Medela UK (26969), The Nursery Store (63666), Chicco (99689), Tutti Bambini (103277) and Cybex UK (103291). The diagnostic labels other relationships as `not_joined_or_other`, not definitely eligible to apply.

Implementation: `scripts/awin-baby-audit.py` and `.github/workflows/awin-baby-audit.yml` on `codex/awin-deals`. The branch-scoped trial uses only AWIN secrets and no database credentials. It queries programme membership, resolves baby advertiser IDs and fetches bounded paginated offers with redirects disabled. The production collector remains joined-only. No documented baby keyword filter or advertiser-join operation was found in the reviewed publisher endpoints; membership actions remain account-side.

Documentation: [Programme information](https://help.awin.com/apidocs/get-program-information), [Retrieve offers](https://help.awin.com/apidocs/promotions). The offer endpoint supports advertiser, membership, region, activity and offer-type filtering. Unjoined advertisers may omit voucher codes.

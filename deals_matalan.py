"""Bounded, reviewed uniform pilot. Public HTML only; no account or checkout.

One exact product/size keeps the initial owner decision small. Expanding the
recipe requires reviewed identity/terms evidence, not catalogue-wide crawling.
"""
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.matalan.co.uk/c/offers/school-uniform/"
PRODUCT_URL = "https://www.matalan.co.uk/p/childrens-clothing/2-pack-kids-black-school-knit-jumpers-3-13yrs/14894526/"
VARIANT = "14894527"
OFFER_URL = PRODUCT_URL + "?variation=" + VARIANT
DELIVERY_URL = "https://www.matalan.co.uk/c/customer-services/delivery/"
TERMS_URL = "https://www.matalan.co.uk/c/customer-services/terms-and-conditions/promotions/"
# Conservative stop at the start of the advertised final date: “19.10.26 at
# Midnight” is ambiguous. Never infer an extension from a remaining sale badge.
VALID_UNTIL = "2026-10-18T23:00:00Z"
MAX_BYTES = 6000000
TITLE = "2 Pack Kids Black School Knit Jumpers (3-13yrs) - Age 4 Years"
DELIVERY = ("Online only. Item price £{current:.2f} excludes fulfilment. Standard home delivery £3.99 "
            "(£{home:.2f} total for this item alone); free on orders over £49.99. Standard click & collect "
            "£0.99 (£{collect:.2f} total), free over £19.99, subject to store availability. "
            "No combined offers or discount codes. Check checkout and current delivery restrictions.")


def read(url):
    if url not in {SOURCE_URL, PRODUCT_URL, OFFER_URL, DELIVERY_URL, TERMS_URL}:
        return "unsupported_url", ""
    try:
        with requests.get(url, headers={"User-Agent": "DadspaceDealsWorker/0.5"},
                          timeout=(5, 20), allow_redirects=False, stream=True) as response:
            if response.status_code != 200:
                return f"http_{response.status_code}", ""
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                return "unsupported_content", ""
            body = bytearray()
            for chunk in response.iter_content(16384):
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    return "oversize_page", ""
    except requests.RequestException:
        return "network_error", ""
    return "ok", body.decode("utf-8", errors="replace")


def decode(value):
    """Decode Astro's JSON value tuples; never execute merchant JavaScript."""
    if isinstance(value, list) and len(value) == 2 and type(value[0]) is int and value[0] in (0, 1):
        return decode(value[1])
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, dict):
        return {k: decode(v) for k, v in value.items()}
    return value


def money(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    try:
        number = Decimal(str(value))
        return number if number.is_finite() and number > 0 and number == number.quantize(Decimal("0.01")) else None
    except InvalidOperation:
        return None


def parse_product(text):
    soup = BeautifulSoup(text, "html.parser")
    variants = []
    corroboration = []
    try:
        for island in soup.select("astro-island[props]"):
            if "/MarketedSpecialOffer." in island.get("component-url", ""):
                v = decode(json.loads(island["props"])).get("activeVariantData", {})
                if str(v.get("sku")) == VARIANT:
                    variants.append(v)
        for script in soup.select('script[type="application/ld+json"]'):
            data = json.loads(script.get_text())
            if isinstance(data, dict) and data.get("@type") == "ProductGroup" and str(data.get("productGroupID")) == "14894526":
                corroboration.extend(v for v in data.get("hasVariant", []) if str(v.get("sku")) == VARIANT)
        if len(variants) != 1 or len(corroboration) != 1:
            return None
        v, ld = variants[0], corroboration[0]
        choices = {c["optionKey"]: c["key"] for c in v["choices"]}
        price, rrp = v["price"]["price"], v["price"]["rrp"]
        current, comparison = money(price["amount"]), money(rrp["amount"])
        offer = ld["offers"]
        if (v["title"] != TITLE or choices != {"Size": "Age 4 Years", "Colour": "Black"}
                or v.get("inStock") is not True or ld.get("size") != "Age 4 Years" or ld.get("color") != "Black"
                or offer.get("url") != OFFER_URL or str(offer.get("sku")) != VARIANT
                or offer.get("availability") != "https://schema.org/InStock"
                or any(c != "GBP" for c in (price["currency"], rrp["currency"], offer["priceCurrency"]))
                or current is None or comparison is None or comparison <= current
                or money(offer["price"]) != current):
            return None
        return current, comparison
    except (ValueError, TypeError, KeyError, AttributeError):
        return None


def clean(text):
    soup = BeautifulSoup(text, "html.parser")
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))


def fetch_matalan(source):
    if source.get("url") != SOURCE_URL:
        return "unsupported_url", [], "Unreviewed Matalan route"
    if datetime.now(timezone.utc) >= datetime.fromisoformat(VALID_UNTIL.replace("Z", "+00:00")):
        return "review_expired", [], "Campaign needs fresh terms review"
    pages = {}
    for url in (SOURCE_URL, OFFER_URL, DELIVERY_URL, TERMS_URL):
        status, text = read(url)
        if status != "ok":
            return status, [], "Required merchant evidence unavailable; freshness not renewed"
        pages[url] = text
    links = {a.get("href") for a in BeautifulSoup(pages[SOURCE_URL], "html.parser").select("a[href]")}
    if PRODUCT_URL not in links and PRODUCT_URL.replace("https://www.matalan.co.uk", "") not in links:
        return "product_not_listed", [], "Reviewed product no longer in uniform offers"
    terms, delivery = clean(pages[TERMS_URL]), clean(pages[DELIVERY_URL])
    campaign = re.search(r"20% Off \(Almost\) Everything - Online Only (.{0,1000})", terms)
    required = ("19.10.26 at Midnight", "online and via the APP only", "Cannot be used in conjunction")
    if not campaign or any(t not in campaign.group(1) for t in required):
        return "terms_changed", [], "Campaign conditions need review"
    if any(t not in delivery for t in ("Standard Home Delivery (£3.99)", "Orders Over £49.99", "Standard Click & Collect (£0.99 or Free for Orders Over £19.99)")):
        return "delivery_changed", [], "Delivery costs need review"
    prices = parse_product(pages[OFFER_URL])
    if not prices:
        return "variant_unconfirmed", [], "Exact size, stock and prices not corroborated"
    current, comparison = prices
    # Fulfilment totals must follow the live price, rather than a frozen example.
    description = ("Two school-uniform jumpers; black, age 4 years. " + DELIVERY.format(
                   current=current, home=current + Decimal('3.99'), collect=current + Decimal('0.99'))
                   + " Delivery terms: " + DELIVERY_URL + " Promotion terms: " + TERMS_URL
                   + " Merchant-advertised RRP comparison; not independently verified as a previous selling price.")
    from deals_source_adapters import _raw
    raw = _raw(title=TITLE, description=description, link=OFFER_URL, merchant="Matalan",
               price=float(current), identity="matalan:14894526:" + VARIANT)
    raw.update(matalan_variant_id=VARIANT, taxonomy_item_label="School uniform sweaters",
               comparison_basis="merchant_advertised", merchant_comparison_price=float(comparison),
               value_evidence_status="merchant_advertised", expires_at=VALID_UNTIL)
    return "ok", [raw], "One exact uniform variant corroborated; no checkout or independent history claim"


def verify_matalan(deal):
    if deal.get("link") != OFFER_URL or deal.get("matalan_variant_id") != VARIANT:
        return "verification_unsupported_source", None
    status, rows, _ = fetch_matalan({"url": SOURCE_URL})
    if status != "ok" or len(rows) != 1:
        return "matalan_" + status, None
    row = rows[0]
    if (money(row["merchant_price"]) != money(deal.get("price")) or money(row["merchant_comparison_price"]) != money(deal.get("was_price"))
            or deal.get("value_evidence_status") != "merchant_advertised" or deal.get("expires_at") != VALID_UNTIL):
        return "matalan_evidence_changed", None
    return None, "source-page:merchant-advertised"

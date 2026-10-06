"""Two reviewed public Shopify collection feeds; no Admin API or browser dependency.

Catalogue compare-at prices deliberately never establish a verified saving.
Only embedded product JSON is read; merchant JavaScript is never executed.
"""
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import requests

SHOPS = {
    "https://kite-clothing.co.uk/collections/baby-children-outlet.atom": {
        "name": "Kite Clothing", "host": "kite-clothing.co.uk",
        "delivery": "UK delivery: £4 below £60; free over £60. Check current delivery terms and size availability.",
        "delivery_url": "https://kite-clothing.co.uk/pages/delivery",
        "keywords": ["baby", "children", "clothing", "hat", "leggings"],
    },
    "https://babymori.com/collections/sale.atom": {
        "name": "MORI", "host": "babymori.com",
        "delivery": "UK standard Evri delivery: £4.50; free over £75. UK islands have different charges. Check current delivery terms.",
        "delivery_url": "https://babymori.com/pages/delivery",
        "keywords": ["baby", "children", "sleepsuit", "pyjamas", "sleeping bag"],
    },
}
MAX_PAGES = 2
MAX_PRODUCTS = 12
MAX_BYTES = 4500000
AGENT = "DadspaceDealsWorker/0.5"


def reviewed_comparison(raw, product, text):
    """Only time-bounded, reviewed variant evidence corroborated on the live page.

    The review file is versioned, contains no credentials and starts empty.
    A review entry needs an exact merchant regular-price phrase, not compare-at JSON.
    """
    records = json.loads(Path(__file__).with_name("shopify-value-reviews.json").read_text(encoding="utf-8"))
    evidence = records.get(raw["identity"])
    if not evidence:
        return
    try:
        expires = datetime.fromisoformat(evidence["valid_until"].replace("Z", "+00:00"))
        regular = evidence["regular_price"]
        expected = evidence["current_price"]
        phrase = evidence["regular_price_phrase"]
        clean = html.unescape(re.sub(r"<[^>]*>", " ", text))
        normalize = lambda v: re.sub(r"\s+", " ", v).strip()
        if (not evidence.get("reviewer") or not evidence.get("evidence_url") or
                expires.tzinfo is None or expires <= datetime.now(timezone.utc) or
                isinstance(regular, bool) or not isinstance(regular, (int, float)) or
                not isinstance(expected, (int, float)) or expected != float(raw["merchant_price"]) or
                not isinstance(phrase, str) or not re.search(r"\b(?:was|regular price)\b", phrase, re.I) or
                f"£{regular:g}" not in phrase or normalize(phrase) not in normalize(clean) or
                regular <= expected):
            return
    except (KeyError, TypeError, ValueError):
        return
    raw.update(comparison_basis="retailer_regular", merchant_comparison_price=regular,
               value_evidence_status="reviewed", expires_at=evidence["valid_until"])


def allowed(url, shop):
    try:
        p = urlsplit(url)
        return (p.scheme == "https" and p.hostname == shop["host"] and
                p.port in (None, 443) and not p.username and not p.password and
                not p.fragment and ((re.fullmatch(r"/products/[a-z0-9-]+", p.path) and
                                     (not p.query or re.fullmatch(r"variant=\d+", p.query))) or
                any(url == feed or re.fullmatch(re.escape(feed) + r"\?page=[12]", url)
                    for feed, entry in SHOPS.items() if entry is shop)))
    except ValueError:
        return False


def read(url, shop):
    if not allowed(url, shop):
        return "unsupported_url", ""
    for attempt in range(2):
        try:
            with requests.get(url, headers={"User-Agent": AGENT}, timeout=(5, 15),
                              allow_redirects=False, stream=True) as response:
                if response.status_code in (429, 502, 503) and attempt == 0:
                    time.sleep(1)
                    continue
                if response.status_code != 200:
                    return f"http_{response.status_code}", ""
                body = bytearray()
                for chunk in response.iter_content(32768):
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        return "oversize_page", ""
                text = body.decode("utf-8", errors="replace")
                if re.search(r"<title>\s*(?:Just a moment|Access denied|Attention Required)", text, re.I):
                    return "blocked_page", ""
                return "ok", text
        except requests.RequestException:
            if attempt == 0:
                time.sleep(1)
    return "network_error", ""


def product_json(text, handle):
    decoder = json.JSONDecoder()
    candidates = []
    # Themes expose complete product JSON either in a JSON script or an assignment.
    # Decode objects without evaluating scripts; verify exact handle and structure.
    for block in re.findall(r"<script\b[^>]*>(.*?)</script>", text, re.I | re.S):
        for match in re.finditer(r'\{\s*"(?:id|handle)"\s*:', block):
            try:
                value, _ = decoder.raw_decode(block[match.start():])
            except ValueError:
                continue
            if (isinstance(value, dict) and value.get("handle") == handle and
                    value.get("id") and value.get("title") and isinstance(value.get("variants"), list) and
                    value["variants"] and all(isinstance(v, dict) and isinstance(v.get("price"), int)
                                               and not isinstance(v.get("price"), bool) and "available" in v
                                               for v in value["variants"])):
                candidates.append(value)
    if not candidates:
        return None
    def description(value):
        desc = value.get("description")
        return clean_text(desc) if isinstance(desc, str) else ""
    # Analytics/theme summaries can have placeholder descriptions. Prefer the
    # complete product object, then same-product JSON-LD as a description fallback.
    product = dict(max(candidates, key=lambda value: len(description(value))))
    for block in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.I | re.S):
        try:
            value = json.loads(block)
        except ValueError:
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            if (isinstance(item, dict) and item.get("@type") == "Product" and
                    urlsplit(str(item.get("url", ""))).path == "/products/" + handle and
                    item.get("name") == product["title"] and
                    len(description(item)) > len(description(product))):
                product["description"] = item["description"]
    product["description"] = description(product)
    return product


def clean_text(value):
    value = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", value, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value))).strip()


def taxonomy_label(product):
    """Reviewed merchant types resolve to the existing canonical labels/IDs.

    Unknown types are left for review, not assigned to a catch-all category.
    """
    kind = str(product.get("type", "")).strip().lower()
    direct = {"hats": "Kids hats", "mittens": "Kids mittens", "gloves": "Kids gloves",
              "trousers": "Kids trousers", "leggings": "Kids leggings", "pyjamas": "Kids pajamas",
              "pajamas": "Kids pajamas", "sleepsuits": "Baby sleepers", "socks": "Kids socks",
              "t-shirts": "Kids T-shirts", "shirts": "Kids shirts", "jumpers": "Kids sweaters"}
    if kind in direct:
        return direct[kind]
    text = (product["title"] + " " + product.get("description", "")).lower()
    if kind == "outerwear":
        if re.search(r"\b(?:waterproof|raincoat|splash coat)\b", text):
            return "Kids raincoats"
        if re.search(r"\b(?:winter|padded|quilted|insulat\w*|cocoon|warm|fleece lined)\b", text):
            return "Kids winter coats"
    return None


def gbp(text):
    active = re.search(r"Shopify\.currency\s*=\s*\{\s*['\"]active['\"]\s*:\s*['\"]([A-Z]{3})", text)
    if active:
        return active.group(1) == "GBP"
    declared = re.findall(r"(?:currency\s*[=:]\s*['\"]|currency['\"]\s*:\s*['\"]|priceCurrency['\"]\s*:\s*['\"])([A-Z]{3})", text)
    return bool(declared) and set(declared) == {"GBP"}


def rows(product, url, shop):
    from deals_source_adapters import _raw
    out = []
    for variant in product["variants"][:250]:
        if not isinstance(variant, dict) or not str(variant.get("id", "")).isdecimal():
            continue
        price = variant.get("price")
        if isinstance(price, bool) or not isinstance(price, int) or price < 0:
            continue
        vid = str(variant["id"])
        title = f"{product['title']} — {variant.get('title', 'Default')}"
        age = re.search(r"(?:^|/)\s*(\d{1,2})(?:\s*-\s*(\d{1,2}))?\s*(months?|m|years?|y)\b",
                        str(variant.get("title", "")), re.I)
        child = False
        audience_invalid = bool(re.search(r"\b(?:men'?s|women'?s|adult)\b", product["title"], re.I))
        if age:
            lower, upper = int(age[1]), int(age[2] or age[1])
            months = age[3].lower().startswith("m")
            if lower <= upper and ((months and upper <= 24) or (not months and upper <= 12)):
                title = ("Baby " if months else "Children's ") + title
                child = True
            else:
                audience_invalid = True
        description = clean_text(product.get("description") or "")
        # Do not copy marketing/RRP/compare-at amounts into the value parser.
        description = re.sub(r"£\s*[\d,.]+", "[unverified amount]", description)
        comparison = variant.get("compare_at_price")
        sale = (isinstance(comparison, int) and not isinstance(comparison, bool) and comparison > price > 0)
        claim = ("Merchant-advertised sale offer. The merchant's comparison price is not independently verified as a previous selling price."
                 if sale else "No supported sale comparison supplied.")
        image = product.get("featured_image") or product.get("image")
        if isinstance(image, dict):
            image = image.get("src") or image.get("url")
        if isinstance(image, str) and image.startswith("//"):
            image = "https:" + image
        if not isinstance(image, str) or urlsplit(image).scheme != "https":
            image = None
        raw = _raw(title=title, description=description[:3000] + " " + shop["delivery"] +
                   " Delivery terms: " + shop["delivery_url"] +
                   " " + claim,
                   link=url + "?variant=" + vid, merchant=shop["name"], price=price / 100,
                   image=image,
                   guid=f"shopify:{shop['host']}:{product['id']}:{vid}",
                   identity=f"shopify:{shop['host']}:{product['id']}:{vid}",
                   status="active" if variant.get("available") is True and not variant.get("requires_selling_plan") else "unavailable")
        raw["shopify_variant_id"] = vid
        raw["shopify_compare_at_price"] = variant.get("compare_at_price")
        raw["shopify_audience_invalid"] = audience_invalid
        raw["taxonomy_item_label"] = taxonomy_label(product) if child and not audience_invalid else None
        raw["value_evidence_status"] = "merchant_advertised" if sale else "unsupported_shopify_comparison"
        if sale:
            raw["comparison_basis"] = "merchant_advertised"
            raw["merchant_comparison_price"] = comparison / 100
        out.append(raw)
    return out


def fetch_shopify(source):
    feed = source.get("url")
    shop = SHOPS.get(feed)
    if not shop:
        return "unsupported_url", [], "Shopify merchant/collection has not been reviewed"
    links, signatures = [], set()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for page in range(1, MAX_PAGES + 1):
        status, text = read(feed if page == 1 else feed + f"?page={page}", shop)
        if status != "ok":
            return status, [], "Collection unavailable; no freshness renewed"
        if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
            return "invalid_feed", [], "Unsafe XML declaration"
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return "invalid_feed", [], "Invalid Atom feed"
        if root.tag != "{http://www.w3.org/2005/Atom}feed":
            return "invalid_feed", [], "Expected Atom collection"
        entries = root.findall("a:entry", ns)
        found = [link.get("href") for entry in entries for link in entry.findall("a:link", ns)
                 if link.get("rel", "alternate") == "alternate" and allowed(link.get("href", ""), shop)]
        signature = tuple(found)
        if found and signature in signatures:
            return "incomplete", [], "Collection repeated a page"
        signatures.add(signature)
        links.extend(url for url in found if url not in links)
        if len(links) >= MAX_PRODUCTS or not entries:
            break
    out = []
    for url in links[:MAX_PRODUCTS]:
        time.sleep(0.2)
        status, text = read(url, shop)
        if status != "ok":
            return status, [], "Product unavailable; no partial batch published"
        if not re.search(r"cdn\.shopify\.com|Shopify\.shop|/cdn/shop/", text):
            return "platform_unconfirmed", [], "Expected Shopify product page"
        product = product_json(text, urlsplit(url).path.rsplit("/", 1)[-1])
        if not product or not gbp(text):
            return "product_unconfirmed", [], "Complete variant data/GBP evidence missing"
        if len(product["variants"]) > 250:
            return "incomplete", [], "Variant limit exceeded; no partial batch published"
        variants = rows(product, url, shop)
        for raw in variants:
            reviewed_comparison(raw, product, text)
        out.extend(variants)
    return ("ok" if out else "empty"), out, (f"Reviewed Shopify catalogue: {len(links[:MAX_PRODUCTS])} products, {len(out)} variants; "
                                              f"bounded sample (not full catalogue); sale comparisons are merchant-advertised")


def verify_shopify(deal, pages=None):
    from urllib.parse import parse_qs
    p = urlsplit(deal["link"])
    shop = next((s for s in SHOPS.values() if s["host"] == p.hostname), None)
    variant = parse_qs(p.query).get("variant", [])
    if not shop or not allowed(deal["link"], shop) or len(variant) != 1 or variant[0] != deal.get("shopify_variant_id"):
        return "verification_unsupported_source", None
    url = f"https://{p.hostname}{p.path}"
    if pages is not None and url in pages:
        status, text = pages[url]
    else:
        status, text = read(url, shop)
        if pages is not None:
            pages[url] = status, text
    if status != "ok":
        return "verification_unavailable", None
    product = product_json(text, p.path.rsplit("/", 1)[-1])
    if not product or not gbp(text):
        return "verification_unavailable", None
    row = next((r for r in rows(product, url, shop) if r["shopify_variant_id"] == variant[0]), None)
    if not row or row["source_status"] != "active":
        return "source_unavailable", None
    if float(row["merchant_price"]) != deal.get("price"):
        return "price_changed", None
    reviewed_comparison(row, product, text)
    if row["value_evidence_status"] not in {"reviewed", "merchant_advertised"} or row.get("merchant_comparison_price") != deal.get("was_price"):
        return "comparison_unconfirmed", None
    if row["value_evidence_status"] != deal.get("value_evidence_status"):
        return "comparison_unconfirmed", None
    if row["shopify_audience_invalid"]:
        return "outside_audience", None
    return None, ("source-page:merchant-advertised" if row["value_evidence_status"] == "merchant_advertised" else "source-page")

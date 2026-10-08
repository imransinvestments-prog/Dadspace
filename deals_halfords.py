"""Free public Halfords product data, bounded and checked without browser/AI."""
import html
import json
import re
from urllib.parse import urlsplit
import requests

SOURCE_URL = "https://www.halfords.com/bikes/kids-bikes/"


def allowed(url):
    parts = urlsplit(url)
    return parts.scheme == "https" and parts.hostname == "www.halfords.com" and parts.port in (None, 443) and not parts.username and not parts.password and (url == SOURCE_URL or parts.path.startswith(("/bikes/kids-bikes/", "/bikes/junior-bikes/", "/bikes/balance-bikes/")))


def read_page(url):
    if not allowed(url):
        return "unsupported_url", ""
    try:
        with requests.get(url, headers={"User-Agent": "DadspaceDealsWorker/0.4"}, timeout=(5, 15), allow_redirects=False, stream=True) as r:
            if r.status_code != 200:
                return f"http_{r.status_code}", ""
            body = bytearray()
            for chunk in r.iter_content(32768):
                body.extend(chunk)
                if len(body) > 4500000:
                    return "oversize_page", ""
    except requests.RequestException:
        return "network_error", ""
    text = body.decode("utf-8", errors="replace")
    if re.search(r"<title>\s*(?:Just a moment|Access Denied|Attention Required)", text, re.I):
        return "blocked_page", ""
    return "ok", text


def products(text):
    found = {}
    stock_ids = set()
    for url, availability in re.findall(r'"url"\s*:\s*"(https://www\.halfords\.com/bikes/[^"<>]+)".{0,600}?"availability"\s*:\s*"([^"]+)"', text):
        match = re.search(r'-(\d+)\.html', url)
        if match and availability == "https://schema.org/InStock":
            stock_ids.add(match.group(1))
    def walk(value):
        if isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            if value.get("pid") and value.get("sale_price") is not None:
                url = value.get("url", "")
                if allowed(url):
                    pid = str(value["pid"])
                    found[pid] = {"id": pid, "productName": value.get("title"), "price": {"sales": {"value": value.get("sale_price"), "currency": "GBP"}, "list": {"value": value.get("price"), "currency": "GBP"}}, "availability": {"isInStock": True}, "available": True, "listing_only": True, "url": url, "image": value.get("thumb_image")}
            elif value.get("id") and isinstance(value.get("c_defaultPrice"), dict):
                pid = str(value["id"])
                stock = pid in stock_ids
                found[pid] = {"id": pid, "productName": value.get("name"), "price": value["c_defaultPrice"], "availability": {"isInStock": stock}, "available": value.get("c_productAvailable") is True}
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child)
    for block in re.findall(r"<script[^>]*>(.*?)</script>", text, re.I | re.S):
        try:
            data = json.loads(block.strip())
        except (ValueError, TypeError):
            continue
        product = data.get("product") if isinstance(data, dict) else None
        if isinstance(product, dict) and product.get("id"):
            found[str(product["id"])] = product
        walk(data)
    return list(found.values())


def offer(product):
    price = product.get("price") or {}
    sale, regular = price.get("sales") or {}, price.get("list") or {}
    availability = product.get("availability") or {}
    try:
        current, comparison = float(sale["value"]), float(regular["value"])
        saving = comparison-current
        if price.get("saveLabel"):
            saving = float(re.search(r"save\s*£\s*([\d,.]+)", price["saveLabel"], re.I).group(1).replace(",", ""))
    except (TypeError, ValueError, KeyError, AttributeError):
        return None
    # Regular retailer price with an explicit matching saving; never infer from RRP.
    if sale.get("currency") != "GBP" or regular.get("currency") != "GBP" or sale.get("isTradePrice") or current < 0 or comparison <= current or abs(saving-(comparison-current)) > .02:
        return None
    if availability.get("isInStock") is not True or product.get("available") is not True:
        return None
    return current, comparison


def product_link(product, text):
    pid = re.escape(str(product["id"]))
    pattern = r'https://www\.halfords\.com/bikes/kids-bikes/[^"\s<>]*-' + pid + r'\.html'
    match = re.search(pattern, html.unescape(text))
    return match.group(0) if match else None


def fetch_halfords(source):
    from deals_source_adapters import _raw
    status, text = read_page(source.get("url", ""))
    if status != "ok":
        return status, [], "Retailer listing unavailable"
    result = []
    for product in products(text):
        link = product.get("url") or product_link(product, text)
        amounts = offer(product)
        if not link or not amounts:
            continue
        current, comparison = amounts
        title = html.unescape(str(product.get("productName") or ""))
        if not re.search(r"\b(?:kids?|child(?:ren)?|junior|balance)\b", title, re.I):
            continue
        raw = _raw(title=title, price=current, merchant="Halfords", link=link, identity="halfords:"+str(product["id"]),
                   description=f"Halfords lists this model at £{current:.2f} alongside its regular-price comparison of £{comparison:.2f}, saving £{comparison-current:.2f}. Check wheel size and the child's fit before buying. Delivery, store collection and optional assembly depend on your location; check their costs and availability on the retailer page. Intervening prices may have been charged. No finance or trade-only price is used.")
        raw["image_url"] = product.get("image")
        raw["merchant_comparison_price"] = comparison
        raw["comparison_basis"] = "retailer_regular"
        raw["merchant_product_id"] = str(product["id"])
        result.append(raw)
        if len(result) >= 50:
            break
    return ("ok" if result else "empty"), result, f"{len(result)} child-bike price comparisons; individual pages require verification"


def verify_halfords(deal):
    status, text = read_page(deal["link"])
    if status in {"http_404", "http_410"}:
        return "source_unavailable", None
    if status != "ok":
        return "verification_unavailable", None
    for product in products(text):
        if str(product["id"]) != str(deal.get("merchant_product_id")):
            continue
        if product.get("listing_only"):
            continue  # Search data alone never renews a product's freshness.
        prices = offer(product)
        if not prices:
            return "source_unavailable", None
        if prices != (deal["price"], deal["was_price"]):
            return "verification_price_changed", None
        return None, "source-page"
    return "verification_unavailable", None

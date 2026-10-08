"""Source-appropriate checks. Never equate a page response with checkout verification."""
import json
import re
from urllib.parse import urlsplit
import requests


def verify_offer(deal, shopify_pages=None):
    if deal.get("shopify_variant_id"):
        from deals_shopify import verify_shopify
        return verify_shopify(deal, shopify_pages)
    if deal.get("merchant_product_id"):
        from deals_halfords import allowed, verify_halfords
        if allowed(deal["link"]):
            return verify_halfords(deal)
    if deal.get("verified_source_page") == deal.get("link"):
        from deals_direct_sources import RECIPES
        if deal["link"] in RECIPES:
            return None, "source-page"
    if deal.get("source_status") == "active":
        return None, "source-api"  # Explicit current provider status, not a merchant claim.
    url = urlsplit(deal["link"])
    # Only fetch the supported public source. Do not follow arbitrary URLs or redirects.
    if url.scheme != "https" or url.hostname not in {"www.hotukdeals.com", "hotukdeals.com"} or url.port not in (None, 443) or not url.path.startswith("/deals/"):
        return "verification_unsupported_source", None
    try:
        with requests.get(deal["link"], timeout=(5, 10), allow_redirects=False, stream=True,
                          headers={"User-Agent": "DadspaceDealsWorker/0.3"}) as response:
            if response.status_code in (404, 410):
                return "source_unavailable", None
            if response.status_code != 200:
                return "verification_unavailable", None
            body = bytearray()
            for chunk in response.iter_content(16384):
                body.extend(chunk)
                if len(body) >= 512000:
                    break
    except requests.RequestException:
        return "verification_unavailable", None
    text = body.decode("utf-8", errors="replace")
    if re.search(r"<title>\s*(?:Just a moment|Access denied|Attention Required)", text, re.I):
        return "verification_unavailable", None
    # The expected offer title must appear, not a successful error/challenge page.
    import html
    clean = html.unescape(re.sub(r"<[^>]+>", " ", text))
    normalize = lambda value: re.sub(r"\s+", " ", value).strip().lower()
    if normalize(deal["title"]) not in normalize(clean):
        return "verification_unavailable", None
    for block in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.I | re.S):
        try:
            data = json.loads(block)
        except (ValueError, TypeError):
            continue
        pending = [data]
        while pending:
            item = pending.pop()
            if isinstance(item, list):
                pending.extend(item)
            elif isinstance(item, dict):
                if str(item.get("availability", "")).rsplit("/", 1)[-1] in {"OutOfStock", "SoldOut", "Discontinued"}:
                    return "source_unavailable", None
                pending.extend(value for value in item.values() if isinstance(value, (list, dict)))
    return None, "source-page"


def verify_kept(deals, reject, max_checks=120):
    from collections import deque
    # Round-robin sources and canonical items before spending the bounded budget.
    # A clothing store's many size variants must not starve other categories.
    sources = {}
    for deal in deals:
        if deal.get("decision") == "kept":
            items = sources.setdefault(deal.get("source_id"), {})
            items.setdefault(deal.get("item_id") or deal.get("matched_item") or deal.get("link"), deque()).append(deal)
    sources = {source: deque(items.values()) for source, items in sources.items()}
    ordered = []
    while sources:
        for source, items in list(sources.items()):
            variants = items.popleft()
            ordered.append(variants.popleft())
            if variants:
                items.append(variants)
            if not items:
                del sources[source]
    checked = 0
    shopify_pages = {}
    for deal in ordered:
        if checked >= max_checks:
            reject(deal, "verification_budget: retry next run")
            continue
        checked += 1
        reason, method = verify_offer(deal, shopify_pages)
        if reason:
            reject(deal, reason)
        else:
            deal["classified_by"] = deal["classified_by"].replace("quality-v1:", f"quality-v1:{method}:", 1)


#!/usr/bin/env python3
"""Source adapters for Dadspace deals ingestion.

Each adapter returns ``(status, raw_items, info)``. ``raw_items`` deliberately
uses the same shape as the existing RSS parser so the rest of the Dadspace
pipeline stays shared across every source.
"""

import json
import os
from datetime import datetime, timezone
import requests

USER_AGENT = "DadspaceDealsWorker/0.2"


def _text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _first(obj, *names, default=""):
    for name in names:
        value = obj.get(name)
        if value not in (None, "", []):
            return value
    return default


def _iso_to_rfc2822(value):
    if not value:
        return ""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
        except (OverflowError, OSError, ValueError):
            return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%a, %d %b %Y %H:%M:%S %z")
    except (TypeError, ValueError):
        return str(value)


def _raw(*, title, description="", link="", guid="", published="", category="", merchant="", price="", image=""):
    return {
        "title_raw": _text(title).strip(),
        "description_raw": _text(description).strip(),
        "link": _text(link).strip(),
        "guid": _text(guid).strip(),
        "pub_date": _iso_to_rfc2822(published),
        "feed_category": _text(category).strip(),
        "merchant_name": _text(merchant).strip(),
        "merchant_price": _text(price).strip(),
        "image_url": _text(image).strip() or None,
    }


def fetch_awin(source):
    token = os.getenv("AWIN_API_TOKEN", "").strip()
    publisher_id = os.getenv("AWIN_PUBLISHER_ID", "").strip()
    if not token or not publisher_id:
        return "configuration_missing", [], "AWIN_API_TOKEN or AWIN_PUBLISHER_ID not configured"
    default_url = f"https://api.awin.com/publisher/{publisher_id}/promotions"
    url = (source.get("url") or default_url).strip()
    if url == "config://awin":
        url = default_url
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    body = {
        "filters": {"membership": "joined", "region": "GB", "status": "active"},
        "pagination": {"page": 1, "pageSize": 200},
    }
    try:
        response = requests.post(url, headers=headers, json=body, timeout=(10, 45))
    except requests.RequestException as exc:
        return "network_error", [], str(exc)[:180]
    if response.status_code == 429:
        return "rate_limited_429", [], "Awin rate limited (429)"
    if response.status_code in (401, 403):
        return "auth_error", [], f"Awin HTTP {response.status_code}"
    if response.status_code >= 300:
        return f"http_{response.status_code}", [], response.text[:180]

    data = response.json()
    offers = data if isinstance(data, list) else (data.get("offers") or data.get("promotions") or data.get("data") or data.get("results") or [])
    out = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        advertiser = _first(offer, "advertiser", "advertiserName", "merchant", default="")
        if isinstance(advertiser, dict):
            advertiser = _first(advertiser, "name", "advertiserName", default="")
        description = _text(_first(offer, "description", "terms", "details", default=""))
        voucher = _first(offer, "voucherCode", "voucher_code", "code", default="")
        if voucher:
            description = f"{description} Voucher code: {voucher}".strip()
        out.append(_raw(
            title=_first(offer, "title", "name", "headline", default=""),
            description=description,
            link=_first(offer, "trackingUrl", "trackingURL", "deeplink", "url", "link", default=""),
            guid=_first(offer, "id", "promotionId", "offerId", default=""),
            published="",
            category=_first(offer, "category", "promotionCategory", "type", default=""),
            merchant=advertiser,
            price=_first(offer, "salePrice", "price", default=""),
            image=_first(offer, "imageUrl", "image", "logoUrl", default=""),
        ))
    return ("ok" if out else "empty"), out, f"Awin promotions: {len(out)}"


def fetch_fmtc(source):
    token = os.getenv("FMTC_API_TOKEN", "").strip()
    if not token:
        return "configuration_missing", [], "FMTC_API_TOKEN not configured"
    default_url = "https://s3.fmtc.co/api/4.2.0/deals"
    url = (source.get("url") or default_url).strip()
    if url == "config://fmtc":
        url = default_url
    params = {"api_token": token, "format": "JSON", "active": 1, "country": "GB"}
    try:
        response = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=(10, 60))
    except requests.RequestException as exc:
        return "network_error", [], str(exc)[:180]
    if response.status_code == 429:
        return "rate_limited_429", [], "FMTC rate limited (429)"
    if response.status_code in (401, 403):
        return "auth_error", [], f"FMTC HTTP {response.status_code}"
    if response.status_code >= 300:
        return f"http_{response.status_code}", [], response.text[:180]

    data = response.json()
    deals = data if isinstance(data, list) else data.get("data") or data.get("deals") or []
    out = []
    for deal in deals:
        if not isinstance(deal, dict):
            continue
        merchant = deal.get("merchant") or deal.get("merchant_name") or ""
        if isinstance(merchant, dict):
            merchant = _first(merchant, "name", "merchant_name", default="")
        title = _text(_first(deal, "label", "title", "name", default=""))
        sale_price = _first(deal, "sale_price", "price", default="")
        was_price = _first(deal, "was_price", default="")
        percent = _first(deal, "percent", default="")
        if was_price and sale_price and str(was_price) not in {"0", "0.00"}:
            title = f"{title} was £{was_price} now £{sale_price}"
        elif percent and str(percent) not in {"0", "0.0"}:
            title = f"{title} {percent}% off"
        code = _first(deal, "coupon_code", "code", default="")
        description = _text(_first(deal, "description", "restrictions", default=""))
        if code:
            description = f"{description} Coupon code: {code}".strip()
        categories = deal.get("categories") or []
        if isinstance(categories, list):
            category = ", ".join(_text(c.get("name") if isinstance(c, dict) else c) for c in categories)
        else:
            category = _text(categories)
        out.append(_raw(
            title=title,
            description=description,
            link=_first(deal, "subaffiliate_url", "fmtc_url", "cascading_full_url", "url", default=""),
            guid=_first(deal, "id", "coupon_id", "couponid", default=""),
            published="",
            category=category,
            merchant=merchant,
            price=sale_price,
            image=_first(deal, "image", "image_url", default=""),
        ))
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    total = meta.get("total") if isinstance(meta, dict) else None
    info = f"FMTC active GB deals: {len(out)}" + (f" of {total}" if total is not None else "")
    return ("ok" if out else "empty"), out, info


def fetch_pepper(source):
    """Fetch Pepper/HotUKDeals REST API JSON from deal_sources.url."""
    url = (source.get("url") or "").strip()
    if not url:
        return "configuration_missing", [], "Pepper API endpoint is not configured in deal_sources.url"
    api_key = os.getenv("PEPPER_API_KEY", "").strip()
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-Key"] = api_key
    try:
        response = requests.get(url, headers=headers, timeout=(10, 45))
    except requests.RequestException as exc:
        return "network_error", [], str(exc)[:180]
    if response.status_code == 429:
        return "rate_limited_429", [], "Pepper rate limited (429)"
    if response.status_code in (401, 403):
        return "auth_error", [], f"Pepper HTTP {response.status_code}"
    if response.status_code >= 300:
        return f"http_{response.status_code}", [], response.text[:180]

    data = response.json()
    if isinstance(data, list):
        deals = data
    else:
        payload = data.get("data") or data.get("deals") or data.get("results") or data.get("items") or []
        if isinstance(payload, dict):
            deals = payload.get("items") or payload.get("results") or payload.get("threads") or []
        else:
            deals = payload
    out = []
    for deal in deals:
        if not isinstance(deal, dict):
            continue
        merchant = deal.get("merchant") or deal.get("shop") or deal.get("store") or ""
        if isinstance(merchant, dict):
            merchant = _first(merchant, "name", "title", default="")
        out.append(_raw(
            title=_first(deal, "title", "name", default=""),
            description=_first(deal, "description", "body", "text", default=""),
            link=_first(deal, "url", "link", "dealUrl", "deal_url", default=""),
            guid=_first(deal, "id", "dealId", "thread_id", "uuid", default=""),
            published=_first(deal, "publishedAt", "createdAt", "created_at", "date", default=""),
            category=_first(deal, "category", "categoryName", "group", default=""),
            merchant=merchant,
            price=_first(deal, "price", "currentPrice", "current_price", default=""),
            image=_first(deal, "imageUrl", "image", "image_url", default=""),
        ))
    return ("ok" if out else "empty"), out, f"Pepper API deals: {len(out)}"


def fetch_source(source, rss_fetcher):
    source_type = (source.get("source_type") or "rss").strip().lower()
    if source_type == "rss":
        return rss_fetcher(source)
    if source_type == "awin":
        return fetch_awin(source)
    if source_type == "fmtc":
        return fetch_fmtc(source)
    if source_type in {"pepper", "pepper_api", "hotukdeals_api"}:
        return fetch_pepper(source)
    return "unsupported_source_type", [], f"unsupported source_type={source_type}"

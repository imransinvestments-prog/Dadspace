"""Source-appropriate checks. Never equate a page response with checkout verification."""
import json
import re
from urllib.parse import urlsplit
import requests


def verify_offer(deal):
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


def verify_kept(deals, reject):
    for deal in deals:
        if deal.get("decision") != "kept":
            continue
        reason, method = verify_offer(deal)
        if reason:
            reject(deal, reason)
        else:
            deal["classified_by"] = deal["classified_by"].replace("quality-v1:", f"quality-v1:{method}:", 1)


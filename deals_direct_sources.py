"""Reviewed public merchant pages. No scraping service, browser or AI dependency.

Recipes fail closed when required offer terms change. A readable terms page alone
does not prove a limited-time campaign is currently available.
"""
import html
import re
from urllib.parse import urlsplit
import requests

RECIPES = {
    "https://www.premierinn.com/gb/en/why/food/breakfast.html": {
        "merchant": "Premier Inn",
        "title": "Premier Inn: kids eat free breakfast with a full adult breakfast",
        "required": [r"up to two under[ -]?16s eat breakfast for free", r"adult orders a full Premier Inn Breakfast"],
        "description": "Up to two children under 16 eat breakfast free when an adult orders a full Premier Inn Breakfast or a Meal Deal. Prices vary by restaurant and location; menu items are subject to availability. Check the restaurant's breakfast times, adult price and eligibility before visiting. No room discount is claimed.",
    },
    "https://www.pizzaexpress.com/terms-and-conditions/kids-eat-free": {
        "merchant": "PizzaExpress",
        "title": "PizzaExpress: kids eat free with a full-price adult main",
        "campaign": "https://www.pizzaexpress.com/offers",
        "required": [r"one Piccolo meal", r"purchase of any full-price adult main", r"12 years or below", r"£15 minimum spend", r"one code is required", r"not valid.*?Collection or Delivery"],
        "description": "One Piccolo meal free with a full-price adult main, dine-in only at participating UK pizzerias while the offer is advertised. Suggested for children aged 12 or below. Piccolo drinks cost extra. Claim through the PizzaExpress Club app or a website QR code: one offer per member per day, or one single-use code per offer. A £15 minimum spend applies per checked-in Club member. Cannot combine with most other offers; see the full terms for exceptions. Availability varies by pizzeria. A group service charge applies to groups of seven adults or more.",
    },
}


def page_text(url):
    if url not in RECIPES and url not in {r.get("campaign") for r in RECIPES.values()}:
        return "unsupported_url", ""
    try:
        with requests.get(url, headers={"User-Agent": "DadspaceDealsWorker/0.4"},
                          timeout=(5, 15), allow_redirects=False, stream=True) as response:
            if response.status_code != 200:
                return f"http_{response.status_code}", ""
            body = bytearray()
            for chunk in response.iter_content(16384):
                body.extend(chunk)
                if len(body) > 1500000:
                    return "oversize_page", ""
    except requests.RequestException:
        return "network_error", ""
    text = body.decode("utf-8", errors="replace")
    text = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text)
    if re.search(r"Just a moment|Access Denied|Attention Required", text, re.I):
        return "blocked_page", ""
    return "ok", text


def fetch_direct(source):
    from deals_shopify import SHOPS, fetch_shopify
    if source.get("url") in SHOPS:
        return fetch_shopify(source)
    from deals_halfords import SOURCE_URL, fetch_halfords
    if source.get("url") == SOURCE_URL:
        return fetch_halfords(source)
    from deals_source_adapters import _raw
    url = source.get("url")
    recipe = RECIPES.get(url)
    if not recipe:
        return "unsupported_url", [], "No reviewed merchant recipe"
    status, text = page_text(url)
    if status != "ok":
        return status, [], "Merchant page unavailable; offer freshness not renewed"
    if any(not re.search(pattern, text, re.I) for pattern in recipe["required"]):
        return "terms_changed", [], "Required current terms missing; recipe needs review"
    if recipe.get("campaign"):
        status, campaign = page_text(recipe["campaign"])
        if status != "ok" or not re.search(r"kids\s+eat\s+free", campaign, re.I):
            return "campaign_unconfirmed", [], "Terms exist but live campaign is not advertised"
    raw = _raw(title=recipe["title"], description=recipe["description"], link=url,
               merchant=recipe["merchant"], identity="direct:"+url)
    # Internal provenance produced only after the allowlisted, bounded page check.
    raw["verified_source_page"] = url
    return "ok", [raw], "Reviewed merchant terms and any campaign visibility checked"

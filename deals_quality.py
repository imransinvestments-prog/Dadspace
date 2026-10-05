"""Deterministic offer evidence; source claims are never merchant verification."""
import re
import math
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

VERSION = "quality-v1:"
AMOUNT = r"£\s*(\d[\d,]*(?:\.\d{1,2})?)"
COMPARISON = re.compile(r"\b(was|rrp|usually|originally|next best price)\s*:?\s*" + AMOUNT, re.I)


def canonical_link(link):
    """Remove marketing attribution only; retain variants, codes and destinations."""
    try:
        parts = urlsplit(link.strip())
        port = parts.port
    except (ValueError, TypeError):
        return ""
    if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username or parts.password:
        return ""
    tracking = {"fbclid", "gclid", "msclkid"}
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in tracking]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path,
                      urlencode(sorted(query)), ""))


def number(value):
    try:
        parsed = float(str(value).replace(",", "").replace("£", "").strip())
        return parsed if math.isfinite(parsed) else None
    except (ValueError, TypeError):
        return None


def prices(raw, title, description):
    # Structured adapter prices are stronger than incidental amounts in titles.
    price = number(raw.get("merchant_price"))
    if price is None:
        current = re.search(r"\b(?:now|price)\s*:?\s*" + AMOUNT, title, re.I)
        leading = re.match(r"\s*" + AMOUNT, description)
        amounts = re.findall(AMOUNT, title)
        if current:
            price = number(current.group(1))
        elif leading:
            price = number(leading.group(1))
        elif len(amounts) == 1 and not COMPARISON.search(title):
            price = number(amounts[0])
        # Multiple unlabeled amounts are ambiguous; do not guess.
    comparison = COMPARISON.search(title) or COMPARISON.search(description)
    was = number(comparison.group(2)) if comparison else None
    # RRP is a manufacturer reference, not proof of a previous selling price.
    if comparison and comparison.group(1).lower() == "rrp":
        was = None
    discount = round((was - price) / was * 100, 1) if was and price is not None and 0 <= price < was else None
    return price, was if discount is not None else None, discount


def value_reason(deal):
    """Value is independent of audience relevance and affiliate commission."""
    price, was, pct = deal.get("price"), deal.get("was_price"), deal.get("discount_pct")
    text = deal.get("title", "") + " " + deal.get("description", "")
    if family_benefit(text):
        return None
    if price is None or was is None or pct is None:
        return "unsupported_value: needs an explicit current and comparison price"
    if was <= price or was <= 0 or price < 0:
        return "unsupported_value: invalid comparison"
    pct = (was - price) / was * 100
    saving = was - price
    # Useful absolute savings matter too; avoids rejecting £50 off a car seat.
    if saving >= 10 and pct >= 10:
        return None
    if saving >= 1 and pct >= 20:
        return None
    return "weak_value: needs £10/10% or £1/20% supported savings"


def family_benefit(text):
    benefit = re.search(r"\b(?:kids?|children)\s+(?:eat|go)\s+free\b|\b2\s+for\s+1\s+(?:family\s+)?(?:tickets|admission)\b", text, re.I)
    # Require explicit eligibility, not just a marketing headline.
    terms = re.search(r"\b(?:with (?:a |an )?(?:paying )?adult|per (?:paying )?adult|aged? \d|under \d|adult (?:meal|ticket|admission)|code\s+[a-z0-9]+)\b", text, re.I)
    return benefit.group(0) if benefit and terms else None


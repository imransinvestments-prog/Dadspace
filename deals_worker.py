#!/usr/bin/env python3
"""
Dadspace deals worker.

What it does, in order (the numbers match the pipeline outline):
  5. Fetch every active source in the deal_sources table (RSS feeds).
  6. Check each payload is usable (HTTP 200, valid XML, has items).
  7. Turn each item into one standard shape (price, retailer, image ...).
  8. Check each deal (has a link, sensible price, not too old).
  9. Relevance for dads and parents, in three layers:
       layer 1  keyword rules (free): exclusion words, then the item list
       layer 2  Gemini, ONLY for unclear items that have a child/parent signal
       layer 3  strict acceptance: relevance >= 3 and evidence found in the deal text
     then a value check so only deals that make a difference are kept.
  10. Save (LIVE mode only) and expire old deals.
  12. Write a run summary.

DRY RUN (the default) saves NOTHING to the deals table. It writes review
files into the  review/  folder instead: a summary plus a random sample of
kept and rejected deals, spread across the 8 app groups.

Everything you might want to change is in the "SETTINGS" block below or is
an environment variable set in the workflow file.
"""
import csv
import html
import json
import os
import random
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests
from deals_quality import VERSION, canonical_link, prices, value_reason, family_benefit
from deals_verification import verify_kept

# ---------------------------------------------------------------- SETTINGS
def _env_bool(name, default):
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _env_int(name, default):
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


DRY_RUN = _env_bool("DRY_RUN", True)           # True = save nothing
SAMPLE_SIZE = _env_int("SAMPLE_SIZE", 40)      # size of the review sample
SAMPLE_SEED = _env_int("SAMPLE_SEED", 42)      # same seed = same sample
MIN_PER_GROUP = _env_int("MIN_PER_GROUP", 3)   # at least this many per group
MAX_AGE_DAYS = _env_int("MAX_AGE_DAYS", 30)    # ignore deals posted longer ago
MIN_RELEVANCE = _env_int("MIN_RELEVANCE", 3)   # Gemini score needed (1-5)
GEMINI_BATCH = _env_int("GEMINI_BATCH", 15)    # deals per Gemini call
MAX_GEMINI_ITEMS = _env_int("MAX_GEMINI_ITEMS", 150)  # cap per run
ENABLE_PAID_AI = _env_bool("ENABLE_PAID_AI", False)
DEACTIVATE_AFTER_FAILURES = _env_int("DEACTIVATE_AFTER_FAILURES", 5)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip() or "gemini-2.5-flash"

GROUPS = [
    "Car Seats & Pushchairs",
    "Nursery, Beds & Sleep",
    "Baby & Maternity Essentials",
    "Kids' Clothes & Shoes",
    "Toys, Play & Outdoors",
    "School & Learning",
    "Days Out & Family Fun",
    "Family Home & Safety",
]

HERE = os.path.dirname(os.path.abspath(__file__))
ITEMS_CSV = os.path.join(HERE, "parent_discount_items_clean.csv")
EXCLUSIONS_CSV = os.path.join(HERE, "parent_deal_exclusions.csv")
REVIEW_DIR = "review"
USER_AGENT = "DadspaceDealsWorker/0.1"

NS_PEPPER = "{http://www.pepper.com/rss}"
NS_MEDIA = "{http://search.yahoo.com/mrss/}"

# Words that show a deal is for babies, children or parents
CHILD_RE = re.compile(
    r"(?<![a-z0-9])(baby|babies|infant|infants|newborn|toddler|toddlers|child|children|"
    r"childrens|kid|kids|boy|boys|girl|girls|junior|maternity|pregnancy|pregnant|"
    r"nursing|mum|mums|parent|parents|nursery|school|preschool)(?![a-z0-9])",
    re.I,
)

# Words that are specific enough to accept on their own (UK wording)
STRONG_TERMS = {
    "pushchair", "pram", "nappy", "nappies", "cot", "cot bed", "toddler cot bed",
    "moses basket", "highchair", "isofix base", "stair gate", "safety gate",
    "booster seat", "high back booster", "baby car seat", "group 0+ car seat",
    "i-size car seat", "all stage car seat", "sleepsuit", "babygrow", "dummy",
    "soother", "junior bed", "toddler bed", "travel cot", "playpen", "travel system",
    "pram system", "baby sleeping bag", "swaddle blanket", "changing mat", "run bike",
    "kids scooter", "feeding pillow", "muslin", "muslins", "car seat", "baby monitor",
}

# Keyword value bands for items found by Gemini (matched items use the CSV band)
BIG_WORDS = ["car seat", "pushchair", "pram", "stroller", "travel system", "cot", "crib",
             "bed", "bunk", "mattress", "highchair", "high chair", "monitor", "carrier",
             "bassinet", "playpen", "swing set", "trampoline", "climbing frame",
             "playhouse", "bicycle", "bike", "tablet", "membership", "season pass",
             "wagon", "breast pump", "desk", "luggage", "smartwatch"]
MID_WORDS = ["sterilis", "steriliz", "warmer", "gate", "bath", "bottle", "tickets",
             "admission", "skates", "toys", "set", "blocks", "headphones", "camera",
             "blackout", "humidifier", "rocking", "glider", "dresser", "formula",
             "nappies", "nappy", "wipes", "coat", "snowsuit", "boots", "shoes", "sandbox",
             "paddling", "play gym", "bookshelf"]


STATS = {"gemini_candidates": 0, "gemini_calls": 0, "gemini_errors": 0,
         "tokens_in": 0, "tokens_out": 0}


# ---------------------------------------------------------------- HELPERS
def log(*a):
    print(*a, flush=True)


def now_utc():
    return datetime.now(timezone.utc)


def norm_text(s):
    """Lower-case and tidy punctuation so 'Pram/Stroller' matches 'pram'."""
    s = (s or "").lower().replace("\u2019", "'").replace("'", "")
    s = re.sub(r"[-_/|,:;()\[\]&+]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def has_child_signal(text):
    return bool(CHILD_RE.search(norm_text(text)))


# ------------------------------------------------------------ SUPABASE
_SB_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
_SB_KEY = ""
for _n in ("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY", "SUPABASE_KEY"):
    if os.getenv(_n, "").strip():
        _SB_KEY = os.getenv(_n).strip()
        break
_GEMINI_KEY = ""
for _n in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
    if os.getenv(_n, "").strip():
        _GEMINI_KEY = os.getenv(_n).strip()
        break


def sb(method, path, **kw):
    headers = {"apikey": _SB_KEY, "Authorization": f"Bearer {_SB_KEY}",
               "Content-Type": "application/json"}
    headers.update(kw.pop("headers", {}))
    r = requests.request(method, f"{_SB_URL}/rest/v1/{path}", headers=headers,
                         timeout=30, **kw)
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase {method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text.strip() else None


# ------------------------------------------------------------ LOAD LISTS
def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def compile_items(rows):
    """Turn the active rows of the items list into match patterns."""
    entries, seen = [], {}
    for r in rows:
        if str(r["active"]).strip().lower() not in {"yes", "true", "1"}:
            continue
        terms = [t.strip() for t in r["uk_terms"].split(";") if t.strip()]
        variants = []
        for idx, t in enumerate(terms):
            t_norm = norm_text(t)
            variants.append((idx, t_norm))
            if t_norm.endswith("ies") and len(t_norm) > 5:
                variants.append((idx, t_norm[:-3] + "y"))
            elif t_norm.endswith("s") and not t_norm.endswith("ss") and len(t_norm) > 4:
                variants.append((idx, t_norm[:-1]))
        for idx, t_norm in variants:
            if len(t_norm) < 3:
                continue
            requires_child = str(r.get("needs_child_evidence", False)).lower() in {"true", "yes", "1"}
            strong = not requires_child and (
                (idx == 0 and r["tier"] == "A")
                or t_norm in STRONG_TERMS
                or bool(CHILD_RE.search(t_norm))
            )
            e = {
                "term": t_norm,
                "rx": re.compile(r"(?<![a-z0-9])" + re.escape(t_norm) + r"(?:s|es)?(?![a-z0-9])"),
                "strong": strong,
                "item": r["item_or_service"],
                "group": r["display_group"],
                "tier": r["tier"],
                "band": r["value_band"],
                "item_id": r.get("id"),
                "deal_type": r.get("deal_type", "product"),
                "requires_child": requires_child,
            }
            old = seen.get(t_norm)
            if old is None or (e["strong"] and not old["strong"]):
                seen[t_norm] = e
    entries = list(seen.values())
    entries.sort(key=lambda e: (not e["strong"], -len(e["term"])))  # strong + long first
    return entries


def compile_exclusions(rows):
    out = []
    for r in rows:
        t = norm_text(r["term"])
        if not t:
            continue
        out.append({
            "term": r["term"],
            "mode": r["mode"].strip(),
            "reason": r["reason"],
            "rx": re.compile(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])"),
        })
    return out


# ------------------------------------------------------------ 5/6. FETCH
def fetch_source(src):
    """Returns (status, items, info). status is 'ok', 'empty' or a failure code."""
    url = src["url"]
    last = None
    for attempt in (1, 2):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=(10, 20))
        except requests.exceptions.ConnectTimeout:
            return "timeout", [], "connection timed out (not retried)"
        except requests.exceptions.RequestException as e:
            return "network_error", [], str(e)[:150]
        last = r
        if r.status_code >= 500 and attempt == 1:
            time.sleep(2)
            continue
        break
    if last.status_code == 403:
        return "blocked_403", [], "blocked (403)"
    if last.status_code == 404:
        return "not_found_404", [], "not found (404)"
    if last.status_code == 429:
        return "rate_limited_429", [], "rate limited (429)"
    if last.status_code != 200:
        return f"http_{last.status_code}", [], f"HTTP {last.status_code}"
    try:
        items, info = parse_feed(last.content)
    except ET.ParseError as e:
        return "invalid_xml", [], f"not valid XML: {e}"
    if not items:
        return "empty", [], "feed has 0 items"
    return "ok", items, info


def parse_feed(content):
    root = ET.fromstring(content)
    items, info = [], ""
    for n, it in enumerate(root.findall(".//item")):
        m = it.find(NS_PEPPER + "merchant")
        merchant_attrs = dict(m.attrib) if m is not None else {}
        merchant_text = (m.text or "").strip() if m is not None else ""
        media = it.find(NS_MEDIA + "content")
        if media is None:
            media = it.find(NS_MEDIA + "thumbnail")
        items.append({
            "title_raw": (it.findtext("title") or "").strip(),
            "description_raw": it.findtext("description") or "",
            "link": (it.findtext("link") or "").strip(),
            "guid": (it.findtext("guid") or "").strip(),
            "pub_date": (it.findtext("pubDate") or "").strip(),
            "feed_category": (it.findtext("category") or "").strip(),
            "merchant_name": merchant_attrs.get("name") or merchant_text,
            "merchant_price": merchant_attrs.get("price", ""),
            "image_url": media.attrib.get("url") if media is not None else None,
        })
        if n == 0:
            info = f"first item merchant attributes: {merchant_attrs or merchant_text or 'none'}"
    return items, info


# ------------------------------------------------------------ 7. NORMALISE
POUND_RE = re.compile(r"£\s?(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)")
WAS_RE = re.compile(r"(?:was|rrp|usually|originally|before|next best price)\s*:?\s*£\s?(\d[\d,]*(?:\.\d{1,2})?)", re.I)
PCT_RE = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*%\s*off", re.I)
HEAT_RE = re.compile(r"^\s*(-?\d+)\s*°\s*-\s*")


def money(s):
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def normalise(raw):
    title = raw["title_raw"]
    heat = None
    m = HEAT_RE.match(title)
    if m:
        heat = int(m.group(1))
        title = HEAT_RE.sub("", title, count=1).strip()
    desc = strip_html(raw["description_raw"])[:4000]

    price, was, discount = prices(raw, title, desc)

    posted = None
    if raw["pub_date"]:
        try:
            posted = parsedate_to_datetime(raw["pub_date"])
            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            posted = None

    link = raw["link"].strip()
    return {
        "title": title, "description": desc, "link": link,
        "dedupe_key": raw.get("identity") or canonical_link(link) or raw["guid"], "retailer": raw["merchant_name"] or None,
        "price": price, "was_price": was, "discount_pct": discount, "heat": heat,
        "image_url": raw["image_url"], "posted_at": posted,
        "feed_category": raw["feed_category"],
        "expires_at": raw.get("expires_at"), "starts_at": raw.get("starts_at"),
        "source_status": raw.get("source_status"),
        "verified_source_page": raw.get("verified_source_page"),
        "merchant_product_id": raw.get("merchant_product_id"),
        "shopify_variant_id": raw.get("shopify_variant_id"),
        "value_evidence_status": raw.get("value_evidence_status"),
    }


# ------------------------------------------------------------ 8. VALIDATE
def validate_deal(d):
    if not d["title"]:
        return "missing_title"
    if not canonical_link(d["link"]):
        return "bad_link"
    retailers = {"m&s": "marks and spencer", "marks & spencer": "marks and spencer", "marks and spencer": "marks and spencer", "amazon": "amazon", "argos": "argos", "halfords": "halfords", "ocado": "ocado", "tesco": "tesco", "asda": "asda"}
    claimed = norm_text(d.get("retailer") or "")
    claimed = retailers.get(claimed, claimed)
    explicit = re.search(r"£\s*([\d,.]+)\s+(?:at|from)\s+(marks & spencer|marks and spencer|m&s|amazon|argos|halfords|ocado|tesco|asda)\b", d["description"][:200], re.I)
    if claimed and explicit and money(explicit.group(1)) == d.get("price") and retailers[explicit.group(2).lower()] != claimed:
        return "merchant_conflict: current-price text disagrees with source retailer"
    if d.get("source_status") not in (None, "", "active"):
        return "source_unavailable"
    for field, expired in (("expires_at", True), ("starts_at", False)):
        if d.get(field):
            try:
                date = datetime.fromisoformat(d[field].replace("Z", "+00:00"))
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                if (expired and date <= now_utc()) or (not expired and date > now_utc()):
                    return "expired" if expired else "not_started"
            except (ValueError, TypeError):
                return "invalid_offer_date"
    if re.search(r"\b(?:expired|sold out|out of stock|no longer available)\b", d["title"], re.I):
        return "source_unavailable"
    if d["price"] is not None and (d["price"] < 0 or d["price"] > 10000):
        return "implausible_price"
    if d["posted_at"] and d["posted_at"] < now_utc() - timedelta(days=MAX_AGE_DAYS):
        return "too_old"
    return None


# ------------------------------------------------------------ 9. RELEVANCE
def band_from_title(title):
    t = norm_text(title)
    if any(k in t for k in BIG_WORDS):
        return "big"
    if any(k in t for k in MID_WORDS):
        return "mid"
    return "low"


def layer1_exclusions(d, exclusions):
    """Returns a reason string if the deal must be rejected, else None."""
    title = norm_text(d["title"])
    child = has_child_signal(d["title"])
    for e in exclusions:
        if e["rx"].search(title):
            if e["mode"] == "hard" or not child:
                return f"excluded: {e['term']}"
    return None


def layer1_match(d, entries):
    """Try to match the deal title to the items list.
    Returns ('strong'|'weak', entry) or (None, None)."""
    title = norm_text(d["title"])
    weak = None
    # Prefer the specific item phrase over a shorter, supposedly strong alias.
    for e in sorted(entries, key=lambda e: -len(e["term"])):
        if e["rx"].search(title):
            if e["strong"] or has_child_signal(d["title"] + " " + d["description"]):
                return "strong", e
            if weak is None:
                weak = e
    if weak:
        return "weak", weak
    return None, None


def accept(d, group, matched, tier, band, relevance, evidence, by):
    d.update({"decision": "kept", "reason": "", "display_group": group,
              "matched_item": matched, "tier": tier, "value_band": band,
              "relevance": relevance, "evidence": evidence, "classified_by": VERSION + by})


def reject(d, reason):
    d.update({"decision": "rejected", "reason": reason})


def value_check(d):
    return value_reason(d)


class GeminiError(RuntimeError):
    """A Gemini failure. Carries any tokens that were still used."""
    def __init__(self, msg, tin=0, tout=0):
        super().__init__(msg)
        self.tin, self.tout = tin, tout


def gemini_classify(batch):
    """batch: list of {'id','title','retailer','feed_category'}.
    Returns (answers_by_id, input_tokens, output_tokens)."""
    prompt = (
        "You classify UK shopping deals for Dadspace, an app for dads and parents of "
        "children aged 0 to 12.\n"
        "For each deal decide whether it is a genuinely useful product or family days-out offer for babies, "
        "children up to about 12, or their parents.\n"
        "Include family attraction tickets and kids-eat-free offers with explicit child eligibility. Use Days Out & Family Fun.\n"
        "Reject: pet products, adult-only items, teen (13+) items, second-hand items, "
        "adult-only services, tuition, insurance, general groceries (baby food is fine), games "
        "consoles and video games, cleaning products.\n"
        "Return ONLY a JSON array with one object per deal:\n"
        '{"id": <id>, "relevant": true or false, "group": one of '
        + json.dumps(GROUPS) + ' or "none", "relevance": 1-5, '
        '"evidence": "a short phrase copied EXACTLY from the deal title that shows it '
        'is for babies, children or parents, or empty string"}\n'
        "relevance 5 = clearly for babies/children/parents, 3 = probably, 1 = not at all.\n\n"
        "Deals:\n" + json.dumps(batch, ensure_ascii=False)
    )
    gen_cfg = {"temperature": 0, "responseMimeType": "application/json", "maxOutputTokens": 4096}
    if "2.5-flash" in GEMINI_MODEL:
        gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": gen_cfg}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    last_err = None
    for attempt in (1, 2):
        try:
            r = requests.post(url, headers={"x-goog-api-key": _GEMINI_KEY}, json=body, timeout=(10, 60))
        except requests.exceptions.RequestException as e:
            last_err = str(e)[:150]
            if attempt == 1:
                time.sleep(3)
                continue
            raise RuntimeError(f"Gemini network error: {last_err}")
        if r.status_code in (429, 500, 502, 503) and attempt == 1:
            time.sleep(5)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Gemini HTTP {r.status_code}: {r.text[:200]}")
        break
    data = r.json()
    usage = data.get("usageMetadata", {})
    tin = usage.get("promptTokenCount", 0)
    tout = usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        arr = json.loads(text)
        return {int(a["id"]): a for a in arr if isinstance(a, dict) and "id" in a}, tin, tout
    except Exception as e:  # noqa: BLE001
        raise GeminiError(f"could not read Gemini answer: {e}", tin, tout)


def process_items(deals, entries, exclusions, classify_fn=None):
    """Runs layers 1-3 and the value check on already-validated deals.
    Adds 'decision', 'reason' etc. to each deal. Returns token counts and stats."""
    stats = STATS
    for k in stats:
        stats[k] = 0
    candidates = []
    for d in deals:
        if d.get("decision") == "rejected":
            continue
        why = layer1_exclusions(d, exclusions)
        if why:
            reject(d, why)
            continue
        kind, e = layer1_match(d, entries)
        signal = has_child_signal(d["title"] + " " + d["description"]) or \
            d["feed_category"].lower() == "family & kids"
        benefit = family_benefit(d["title"] + " " + d["description"])
        if benefit:
            accept(d, "Days Out & Family Fun", "", "", "mid", 5, benefit, "rules")
        elif kind == "strong" or (kind == "weak" and signal):
            accept(d, e["group"], e["item"], e["tier"], e["band"], 4, e["term"], "rules")
        elif kind == "weak" and not signal:
            reject(d, "generic_item_no_child_signal")
        elif signal:  # generic item match OR no match, but it has a child/parent signal
            candidates.append(d)
        else:
            reject(d, "no_match_no_child_signal")

    # Layer 2 + 3: Gemini for the unclear ones only
    stats["gemini_candidates"] = len(candidates)
    if candidates:
        if classify_fn is None or not ENABLE_PAID_AI:
            for d in candidates:
                reject(d, "unmapped_item: needs a reviewed taxonomy alias")
        else:
            to_send, over = candidates[:MAX_GEMINI_ITEMS], candidates[MAX_GEMINI_ITEMS:]
            for d in over:
                reject(d, "gemini_skipped (run cap reached)")
            for i in range(0, len(to_send), GEMINI_BATCH):
                chunk = to_send[i:i + GEMINI_BATCH]
                payload = [{"id": n, "title": d["title"], "retailer": d["retailer"] or "",
                            "feed_category": d["feed_category"]} for n, d in enumerate(chunk)]
                try:
                    answers, tin, tout = classify_fn(payload)
                except Exception as ex:  # noqa: BLE001
                    log(f"  Gemini batch failed: {ex}")
                    stats["gemini_errors"] += 1
                    tin, tout = getattr(ex, "tin", 0), getattr(ex, "tout", 0)
                    if tin or tout:  # the call happened and used tokens
                        stats["gemini_calls"] += 1
                        stats["tokens_in"] += tin
                        stats["tokens_out"] += tout
                    for d in chunk:
                        reject(d, "gemini_error")
                    continue
                stats["gemini_calls"] += 1
                stats["tokens_in"] += tin
                stats["tokens_out"] += tout
                for n, d in enumerate(chunk):
                    a = answers.get(n)
                    if not a:
                        reject(d, "gemini_no_answer")
                        continue
                    ev = str(a.get("evidence", "")).strip()
                    rel = int(a.get("relevance", 0) or 0)
                    grp = a.get("group")
                    if not a.get("relevant"):
                        reject(d, "gemini_not_relevant")
                    elif rel < MIN_RELEVANCE:
                        reject(d, f"gemini_low_relevance ({rel})")
                    elif grp not in GROUPS:
                        reject(d, "gemini_bad_group")
                    elif not ev:
                        reject(d, "gemini_no_evidence")
                    elif norm_text(ev) not in norm_text(d["title"] + " " + d["description"]):
                        reject(d, "gemini_evidence_not_in_text")
                    else:
                        accept(d, grp, "", "", band_from_title(d["title"]), rel, ev, "gemini")

    # Value check on everything kept
    for d in deals:
        if d.get("decision") == "kept":
            _, entry = layer1_match(d, entries)
            if family_benefit(d["title"] + " " + d["description"]):
                # Benefits still need a stable taxonomy identity, not a separate hardcoded category.
                entry = next((e for e in entries if e["item"] == "Kids meals at restaurants"), entry) if re.search(r"\beat\s+free\b", d["title"] + " " + d["description"], re.I) else entry
            if entry:
                d["item_id"] = entry.get("item_id")
                d["deal_type"] = entry.get("deal_type")
                d["matched_item"] = entry["item"]
                d["display_group"] = entry["group"]
            why = value_check(d)
            if why:
                reject(d, why)
    return stats


# ------------------------------------------------------------ SAMPLING
def stratified_sample(items, key, total, min_per, seed):
    """Random sample, spread across groups in proportion to their size,
    but with at least min_per from each group (if the group has that many)."""
    if len(items) <= total:
        return list(items)
    rnd = random.Random(seed)
    groups = {}
    for it in sorted(items, key=lambda x: x.get("dedupe_key", "")):
        groups.setdefault(key(it), []).append(it)
    n = len(items)
    alloc = {g: min(len(v), max(min_per, int(total * len(v) / n))) for g, v in groups.items()}
    while sum(alloc.values()) > total:
        g = max((g for g in alloc if alloc[g] > min(min_per, len(groups[g]))), key=lambda g: alloc[g], default=None)
        if g is None:
            break
        alloc[g] -= 1
    while sum(alloc.values()) < total:
        room = [g for g in alloc if alloc[g] < len(groups[g])]
        if not room:
            break
        g = max(room, key=lambda g: len(groups[g]) * total / n - alloc[g])
        alloc[g] += 1
    out = []
    for g, v in groups.items():
        out.extend(rnd.sample(v, alloc[g]))
    return out


# ------------------------------------------------------------ REVIEW FILES
REVIEW_COLS = ["source", "decision", "reason", "display_group", "title", "description", "retailer", "price",
               "was_price", "discount_pct", "heat", "matched_item", "item_id", "deal_type", "tier", "value_band",
               "relevance", "evidence", "classified_by", "link", "expires_at", "starts_at",
               "human_relevant", "human_valuable", "human_terms_clear", "human_link_works",
               "human_not_expired", "human_savings_supported", "reviewer_notes"]


def write_review(all_deals, source_results, stats, started):
    os.makedirs(REVIEW_DIR, exist_ok=True)
    kept = [d for d in all_deals if d.get("decision") == "kept"]
    rejected = [d for d in all_deals if d.get("decision") == "rejected"]

    kept_sample = stratified_sample(kept, lambda d: d["display_group"], SAMPLE_SIZE, MIN_PER_GROUP, SAMPLE_SEED)
    rej_sample = stratified_sample(rejected, lambda d: d["reason"].split(" (")[0].split(":")[0],
                                   SAMPLE_SIZE, 2, SAMPLE_SEED)

    def dump(name, rows):
        with open(os.path.join(REVIEW_DIR, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=REVIEW_COLS, extrasaction="ignore")
            w.writeheader()
            for d in rows:
                w.writerow({c: d.get(c, "") for c in REVIEW_COLS})

    dump("review_kept_sample.csv", sorted(kept_sample, key=lambda d: d["display_group"]))
    dump("review_rejected_sample.csv", sorted(rej_sample, key=lambda d: d["reason"]))
    dump("review_all_decisions.csv", all_deals)

    def count_by(rows, keyf):
        c = {}
        for r in rows:
            c[keyf(r)] = c.get(keyf(r), 0) + 1
        return sorted(c.items(), key=lambda kv: -kv[1])

    lines = []
    A = lines.append
    A("# Dadspace deals: " + ("DRY RUN" if DRY_RUN else "LIVE RUN") + " review")
    A(f"Started {started:%Y-%m-%d %H:%M} UTC. Mode: {'optional AI' if ENABLE_PAID_AI else 'rules-only'}. Sample seed: {SAMPLE_SEED}.\n")
    A("## Sources")
    for s in source_results:
        A(f"- {s['name']}: {s['status']}, {s['items']} items. {s['info']}")
    A("\n## Funnel")
    A(f"- Items fetched: {len(all_deals)}")
    A(f"- Kept: {len(kept)}")
    A(f"- Rejected: {len(rejected)}")
    A(f"- Unclear candidates: {stats['gemini_candidates']}. AI calls: {stats['gemini_calls']} "
      f"({stats['gemini_errors']} failed)")
    A(f"- Tokens: {stats['tokens_in']} in + {stats['tokens_out']} out = "
      f"{stats['tokens_in'] + stats['tokens_out']} total")
    with_price = sum(1 for d in all_deals if d["price"] is not None)
    with_disc = sum(1 for d in all_deals if d["discount_pct"] is not None)
    A(f"- Price found on {with_price} of {len(all_deals)} items; discount found on {with_disc}")
    A("\n## Kept, by group (all / in review sample)")
    samp = dict(count_by(kept_sample, lambda d: d["display_group"]))
    for g, n in count_by(kept, lambda d: d["display_group"]):
        A(f"- {g}: {n} / {samp.get(g, 0)}")
    A("\n## Rejected, by reason")
    for r, n in count_by(rejected, lambda d: d["reason"].split(" (")[0]):
        A(f"- {r}: {n}")
    A("\n## What to check")
    A("1. review_kept_sample.csv: is each one something a parent would want? Is the price right?")
    A("2. review_rejected_sample.csv: are good deals being thrown out? (as important as 1)")
    A("3. Any group with zero or very few deals: does its source feed exist yet?")
    A("4. review_all_decisions.csv has every item if you want to search for something specific.")
    with open(os.path.join(REVIEW_DIR, "review_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log("\n".join(lines))


# ------------------------------------------------------------ SAVE (LIVE)
def save_live(kept, source_id_by_name, reviewed=None):
    now_iso = now_utc().isoformat()
    rows = []
    for d in kept:
        row = {
            "source_id": d["source_id"], "dedupe_key": d["dedupe_key"], "link": d["link"],
            "title": d["title"], "description": d["description"], "retailer": d["retailer"],
            "price": d["price"], "was_price": d["was_price"], "discount_pct": d["discount_pct"],
            "image_url": d["image_url"], "display_group": d["display_group"],
            "matched_item": d["matched_item"] or None, "tier": d["tier"] or None,
            "item_id": d.get("item_id"),
            "value_band": d["value_band"], "relevance": d["relevance"],
            "audience_evidence": d["evidence"], "classified_by": d["classified_by"],
            "heat": d["heat"], "posted_at": d["posted_at"].isoformat() if d["posted_at"] else None,
            "status": "live", "last_seen": now_iso,
        }
        if d.get("expires_at"):
            row["expires_at"] = d["expires_at"]
        rows.append(row)
    # Omitted dates preserve known expiry; uniform keys keep PostgREST batches valid.
    for dated in (False, True):
        batch = [row for row in rows if ("expires_at" in row) == dated]
        for i in range(0, len(batch), 100):
            sb("POST", "deals", params={"on_conflict": "dedupe_key"}, json=batch[i:i + 100],
               headers={"Prefer": "resolution=merge-duplicates,return=minimal"})
    accepted_keys = {d["dedupe_key"] for d in kept}
    for d in reviewed or []:
        if d.get("decision") != "rejected" or d["dedupe_key"] in accepted_keys:
            continue
        reason = d.get("reason", "")
        if reason == "expired":
            patch = {"status": "expired"}
        elif reason.startswith(("unsupported_value", "weak_value", "missing_applicability", "merchant_conflict", "excluded:", "not_started", "invalid_offer_date", "source_unavailable")):
            patch = {"status": "review"}
        else:
            continue  # Missing entries and model/network failures never revoke an offer.
        sb("PATCH", "deals", params={"dedupe_key": "eq." + d["dedupe_key"]}, json=patch,
           headers={"Prefer": "return=minimal"})
    # Feed windows and outages do not establish expiry. Only a known expiry does.
    sb("PATCH", "deals", params={"status": "eq.live", "expires_at": f"lte.{now_iso}"},
       json={"status": "expired"}, headers={"Prefer": "return=minimal"})


def update_source_health(src, status, counts=None):
    failed = status not in ("ok", "empty")
    fails = (src.get("consecutive_failures") or 0) + 1 if failed else 0
    patch = {"last_status": status, "last_checked_at": now_utc().isoformat(),
             "consecutive_failures": fails}
    if not failed:
        patch["last_success_at"] = now_utc().isoformat()
    if counts is not None:
        patch["last_counts"] = counts
        if counts.get("verified", 0):
            patch["last_verified_at"] = now_utc().isoformat()
    # Transient outages remain eligible for a later retry. Do not silently turn off supply.
    sb("PATCH", "deal_sources", params={"id": f"eq.{src['id']}"}, json=patch,
       headers={"Prefer": "return=minimal"})


def stage_of(reason):
    if reason.startswith("gemini"):
        return "gemini"
    if reason.startswith(("unsupported_value", "weak_value", "discount_too_small", "low_value")):
        return "value"
    if reason.startswith("verification") or reason == "source_unavailable":
        return "verification"
    return "prefilter"  # validation or free keyword rules, no Gemini involved


def build_details(all_deals, source_results, started, status="ok", error=None):
    rej = {}
    for d in all_deals:
        if d.get("decision") == "rejected":
            k = d["reason"].split(" (")[0]
            rej[k] = rej.get(k, 0) + 1
    by_group = {}
    for d in all_deals:
        if d.get("decision") == "kept":
            by_group[d["display_group"]] = by_group.get(d["display_group"], 0) + 1
    return {
        "status": status, "error": error, "model": GEMINI_MODEL if ENABLE_PAID_AI else "rules-only",
        "seconds": round((now_utc() - started).total_seconds(), 1),
        "total_tokens": STATS["tokens_in"] + STATS["tokens_out"],
        "gemini_errors": STATS["gemini_errors"],
        "fetched": len(all_deals),
        "kept": sum(1 for d in all_deals if d.get("decision") == "kept"),
        "kept_by_group": by_group, "rejected_by_reason": rej,
        "sources": [{"name": r["name"], "status": r["status"], "items": r["items"]}
                    for r in source_results],
    }


def log_run(skipped_prefilter, details):
    if DRY_RUN:
        log("DRY RUN: pipeline run details are in the local review files; no DB log written.")
        return
    """One row in pipeline_runs, same columns as the news worker."""
    try:
        sb("POST", "pipeline_runs", json={
            "worker": "deals", "dry_run": DRY_RUN,
            "input_tokens": STATS["tokens_in"], "output_tokens": STATS["tokens_out"],
            "gemini_calls": STATS["gemini_calls"],
            "articles_scored": STATS["gemini_candidates"],
            "skipped_prefilter": skipped_prefilter, "details": details,
        }, headers={"Prefer": "return=minimal"})
        log(f"Run logged to pipeline_runs (total tokens: {details['total_tokens']}).")
    except Exception as ex:  # noqa: BLE001
        log(f"(run log to pipeline_runs skipped: {ex})")


# ------------------------------------------------------------ MAIN
def self_test():
    ok = True
    try:
        items = load_csv(ITEMS_CSV)
        entries = compile_items(items)
        ex = compile_exclusions(load_csv(EXCLUSIONS_CSV))
        log(f"OK  lists loaded: {len(items)} items, {len(entries)} match terms, {len(ex)} exclusion terms")
    except Exception as e:  # noqa: BLE001
        log(f"FAIL lists: {e}")
        ok = False
    if not (_SB_URL and _SB_KEY):
        log("FAIL Supabase: SUPABASE_URL or key secret is missing")
        ok = False
    else:
        try:
            rows = sb("GET", "deal_sources", params={"select": "id,name,active", "limit": "50"})
            log(f"OK  Supabase reachable: {len(rows)} sources, {sum(1 for r in rows if r['active'])} active")
        except Exception as e:  # noqa: BLE001
            log(f"FAIL Supabase: {e}")
            ok = False
    log(("OK  " if _GEMINI_KEY else "WARN ") + "Gemini key " + ("found" if _GEMINI_KEY else
        "missing (unclear items will be skipped, not sent to Gemini)"))
    return ok


def run():
    started = now_utc()
    log(f"Deals worker starting. {'DRY RUN (nothing will be saved)' if DRY_RUN else 'LIVE RUN'}")
    if not (_SB_URL and _SB_KEY):
        log("ERROR: SUPABASE_URL / Supabase key secrets are not set in the workflow.")
        return 1
    entries = compile_items(load_csv(ITEMS_CSV))
    exclusions = compile_exclusions(load_csv(EXCLUSIONS_CSV))
    log(f"Loaded {len(entries)} match terms and {len(exclusions)} exclusion terms")

    sources = sb("GET", "deal_sources", params={"select": "*", "active": "eq.true",
                                                "source_type": "eq.rss", "order": "id"})
    log(f"{len(sources)} active sources")

    all_deals, seen_keys, source_results = [], set(), []
    n_fetched = 0
    for src in sources:
        status, raw_items, info = fetch_source(src)
        log(f"- {src['name']}: {status} ({len(raw_items)} items) {info}")
        source_results.append({"name": src["name"], "status": status, "items": len(raw_items), "info": info})
        if not DRY_RUN:
            try:
                update_source_health(src, status)
            except Exception as ex:  # noqa: BLE001
                log(f"  (source health not saved: {ex})")
        for raw in raw_items:
            n_fetched += 1
            d = normalise(raw)
            d.update({"source": src["name"], "source_id": src["id"]})
            why = validate_deal(d)
            if not why and d["dedupe_key"] in seen_keys:
                why = "duplicate"
            if why:
                reject(d, why)
            else:
                seen_keys.add(d["dedupe_key"])
            all_deals.append(d)
        time.sleep(1.5)  # be polite to the source

    stats = process_items(all_deals, entries, exclusions,
                          gemini_classify if _GEMINI_KEY else None)
    verify_kept(all_deals, reject)
    kept = [d for d in all_deals if d.get("decision") == "kept"]
    skips = sum(1 for d in all_deals
                if d.get("decision") == "rejected" and stage_of(d["reason"]) == "prefilter")
    write_review(all_deals, source_results, stats, started)

    if DRY_RUN:
        log("\nDRY RUN: nothing was saved. Download the 'deals-dry-run-review' artifact to review.")
    else:
        save_live(kept, {}, all_deals)
        log(f"\nLIVE: saved {len(kept)} deals and expired only offers with known expiry dates.")
    log_run(skips, build_details(all_deals, source_results, started))
    return 0


if __name__ == "__main__":
    try:
        if "--self-test" in sys.argv:
            sys.exit(0 if self_test() else 1)
        sys.exit(run())
    except Exception as crash:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        if _SB_URL and _SB_KEY:
            log_run(0, {"status": "crashed", "error": str(crash)[:300], "model": GEMINI_MODEL,
                        "total_tokens": STATS["tokens_in"] + STATS["tokens_out"]})
        sys.exit(1)


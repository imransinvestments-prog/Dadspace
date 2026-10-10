#!/usr/bin/env python3
"""
Dadspace news worker.

What it does, in order:
  1. Reads active feeds from the Supabase `news_sources` table.
  2. Fetches each feed and skips articles we've already stored.
  3. Sends new headlines to Gemini in batches to score relevance for UK dads.
  4. Saves everything it scored to `news_items` (the app's `feed_items` view
     only shows relevance 3+, and storing the low scores stops us paying to
     re-score the same headline next time).
  5. Switches off feeds that fail repeatedly, and deletes old articles.

Settings come from environment variables (see the CONFIG section).
Safe by default: DRY_RUN is on unless it is set to "false".

Usage:
  python news_worker.py --self-test    # checks keys and connections only
  python news_worker.py                # normal run
"""

from llm_provider import StructuredGenerator, credential_name, selection, FatalLLMError, BudgetExhausted
import argparse
import html
import json
import os
import re
import sys
import time
import traceback
from calendar import timegm
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests
from news_links import resolve_article_urls

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
def env(name, default=""):
    """Read a setting and remove stray spaces, new lines and quote marks."""
    return os.environ.get(name, default).strip().strip("\"'").strip()


SUPABASE_URL = env("SUPABASE_URL").rstrip("/")
SUPABASE_SERVICE_KEY = env("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = env("GEMINI_API_KEY")
# gemini-2.5-flash is being retired by Google (and is already returning 404
# for some people), so the default is its replacement.
GEMINI_MODEL = env("GEMINI_MODEL") or "gemini-3.5-flash"
# How much hidden "thinking" Gemini does before answering. Thinking is billed as
# output, and the default (medium) is far more than sorting headlines needs.
# Options: minimal, low, medium, high, or "off" to leave it to Google's default.
THINKING_LEVEL = (env("THINKING_LEVEL") or "low").lower()

DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
MIN_RELEVANCE = int(os.environ.get("MIN_RELEVANCE", "3"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "40"))
MAX_ITEMS_PER_FEED = int(os.environ.get("MAX_ITEMS_PER_FEED", "30"))
MAX_NEW_PER_RUN = int(os.environ.get("MAX_NEW_PER_RUN", "300"))
MAX_ARTICLE_AGE_DAYS = int(os.environ.get("MAX_ARTICLE_AGE_DAYS", "14"))
# Preserve every first-ingested article in the current calendar month.
RETENTION_DAYS = max(35, int(os.environ.get("RETENTION_DAYS", "35")))
MAX_FAILURES = int(os.environ.get("MAX_FAILURES", "5"))
MAX_RUN_MINUTES = int(os.environ.get("MAX_RUN_MINUTES", "20"))
MAX_GROUP_ITEMS = int(os.environ.get("MAX_GROUP_ITEMS", "150"))
SNIPPET_CHARS = int(os.environ.get("SNIPPET_CHARS", "160"))
FEED_TIMEOUT = 15
GEMINI_TIMEOUT = 60

USER_AGENT = "Mozilla/5.0 (compatible; DadspaceNewsBot/1.0)"
CATEGORIES = ["policy", "money", "health", "safety", "activities",
              "parenting", "wellbeing", "education", "other"]
REGIONS = ["uk", "england", "scotland", "wales", "northern_ireland"]

PROMPT = """You are the editor of Dadspace, a UK app for fathers of children aged 0-16.
For each article below, decide how useful it is to a UK dad.

Be strict. Only about a third of articles should score 3 or more.

Score "relevance" from 0 to 5:
5 = directly about dads or fatherhood, OR a UK rule, benefit, deadline or product recall that specifically affects children, babies or families and needs action
4 = clearly useful to UK parents of children 0-16: childcare, school life for pupils, child health, family safety, family days out and activities
3 = useful to some parents and has a real, concrete family angle
2 = tangential: general news a parent might glance at but that isn't about families
1 = barely connected
0 = not relevant

Rules of thumb:
- Product recalls and safety reports: 4-5 only if the product is for children or babies, or is a family product used with children (toys, car seats, cots, prams, kids' bikes and scooters, craft kits). Adult or household items (hand wash, tote bags, general appliances) score 1-2. E-bikes and adult scooters score 3.
- Money: general banking, interest rates, mortgages, savings and scam-warning pages score 2 unless the article is specifically about childcare costs, Child Benefit, tax-free childcare, parental leave pay or the cost of raising children.
- Education: rules and changes that affect pupils (GCSEs, school meals, SEND support, screen time, safeguarding, holidays) score 3-4. Anything about staff, academy trust admin, universities, international students, or union disputes scores 0-2, unless school closures are likely.
- Comparisons with other countries and human-interest stories score 2 unless they give a UK dad something practical to do or know.
- Days out, events, holidays and things to do with kids in the UK score 4; generic travel or tourism scores 1-2.
- Employment and workplace law: judge by what it means for dads, not by who it was written for. Articles aimed at employers or HR that explain new rights for parents (parental leave, paternity pay, bereavement leave after pregnancy loss, flexible working) still score 4-5.
- Celebrities and royals talking about fatherhood score 2-3 at most.
- A story that only matters in one town, council or county scores 3 at most, unless it is a UK-wide story.
- The same story from different outlets must get the same score.
- Adverts, sponsored posts, opinion pieces with no family angle, celebrity gossip, sport results and overseas-only news score 0-1.

Also give:
- "category": one of policy, money, health, safety, activities, parenting, wellbeing, education, other
- "region": which part of the UK the article applies to, one of: uk, england, scotland, wales, northern_ireland
    * "uk" = applies across the UK, or isn't tied to one nation (national campaigns, UK-wide rules such as paternity leave, product recalls, general parenting advice)
    * Otherwise the nation it is about, including local stories (a town or council in Wales = "wales"). Education, childcare and health are devolved: Department for Education and NHS England announcements are usually "england"; Welsh Government = "wales"; Scottish Government = "scotland"; Northern Ireland Executive or Department of Education NI = "northern_ireland".
    * If unsure, use "uk".
- "summary": one plain sentence (max 25 words) in your own words
- "why_it_matters": max 15 words, written for a dad
ONLY write "summary" and "why_it_matters" when relevance is 3 or more. For 0-2 use empty strings.

Reply with ONLY a JSON array, one object per article, like:
[{"i": 0, "relevance": 4, "category": "money", "region": "uk", "summary": "...", "why_it_matters": "..."}]

Articles, one per line as: id | source | headline | snippet (snippet may be missing)
"""

# ----------------------------------------------------------------------
# PRE-FILTER (free, runs in code BEFORE anything is sent to Gemini)
# ----------------------------------------------------------------------
# Feeds marked filter_mode = 'keywords' in the sources table must mention at
# least one of these words in the headline/snippet, or they are skipped.
FAMILY_WORDS = re.compile(
    r"\b(child\w*|kid\w*|parent\w*|dad\w*|father\w*|mum|mums|mummy|mother\w*|"
    r"bab(?:y|ies)|infant\w*|toddler\w*|teen\w*|pupil\w*|school\w*|nurser(?:y|ies)|"
    r"famil(?:y|ies)|gcse\w*|a.levels?|sats|send|sen|ofsted|maternity|paternity|"
    r"pregnan\w*|newborn\w*|student\w*|half.term|holidays?)\b",
    re.IGNORECASE)

# Headlines matching these are skipped for EVERY feed (obvious non-starters).
BLOCK_WORDS = re.compile(
    r"\b(obituary|horoscope|premier league|transfer news|match report|betting|odds|"
    r"casino|live blog|as it happened|politics live|share price|stock market|"
    r"crossword|quiz of the)\b",
    re.IGNORECASE)

NEAR_DUPLICATE = 0.6  # share of matching words above which two headlines are "the same"


def prefilter(title, snippet, mode):
    """Return a reason to skip the article, or None to let it through."""
    text = f"{title} {snippet}"
    if BLOCK_WORDS.search(title):
        return "blocked_word"
    if mode == "keywords" and not FAMILY_WORDS.search(text):
        return "no_family_word"
    return None


def word_set(title):
    """Headline reduced to a set of words (publisher suffix removed)."""
    title = re.sub(r"\s+-\s+[^-]{2,40}$", "", title or "")
    return frozenset(w for w in re.findall(r"[a-z0-9]+", title.lower()) if len(w) > 2)


def is_near_duplicate(words, known_sets):
    if len(words) < 4:
        return False
    for other in known_sets:
        if len(other) < 4:
            continue
        overlap = len(words & other) / len(words | other)
        if overlap >= NEAR_DUPLICATE:
            return True
    return False


GROUP_PROMPT = """You are deduplicating a news feed for UK dads. Decide which new articles are about the SAME story, either as each other or as a story already in the feed.

"Same story" means the same specific news event, announcement, law change, product recall, study or campaign, reported by different outlets. Two articles on the same broad topic are NOT the same story: two different toy recalls are two stories, and a paternity-leave protest and a paternity-pay study are two stories.

Existing stories already in the feed, one per line as: key | headline
{existing}

New articles, one per line as: id | headline | source
{new}

Give every new article a "story" key:
- If it is the same story as an existing one, use that existing key exactly.
- Otherwise make up a short lowercase key of 2 to 5 words joined by hyphens (for example smyths-asbestos-recall). Use the SAME new key for every new article about the same story.
- An article that is its own story gets its own unique key.

Reply with ONLY a JSON array like: [{"id": 0, "story": "some-key"}]
"""

START = time.time()
TOKENS = {"in": 0, "out": 0, "think": 0, "calls": 0}  # running Gemini token totals for this run


# ----------------------------------------------------------------------
# SMALL HELPERS
# ----------------------------------------------------------------------
def now_utc():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def out_of_time():
    return (time.time() - START) > MAX_RUN_MINUTES * 60


def clean_text(text, limit=400):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def clean_url(url):
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query)
             if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def title_key(title):
    """Normalised headline, used to catch the same story from several outlets."""
    title = re.sub(r"\s+-\s+[^-]{2,40}$", "", title or "")  # drop " - Publisher"
    return re.sub(r"[^a-z0-9]", "", title.lower())


def entry_date(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(timegm(parsed), tz=timezone.utc)


# ----------------------------------------------------------------------
# SUPABASE
# ----------------------------------------------------------------------
def sb(method, path, params=None, json_body=None, extra_headers=None):
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Content-Type": "application/json",
    }
    # Older Supabase keys (start "eyJ") go in both headers. Newer keys
    # (start "sb_secret_") must ONLY go in "apikey", or Supabase returns 401.
    if SUPABASE_SERVICE_KEY.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {SUPABASE_SERVICE_KEY}"
    if extra_headers:
        headers.update(extra_headers)
    r = requests.request(method, f"{SUPABASE_URL}/rest/v1/{path}",
                         headers=headers, params=params, json=json_body, timeout=30)
    r.raise_for_status()
    return r


def load_sources():
    r = sb("GET", "news_sources", params={"active": "eq.true", "select": "*", "order": "id"})
    return r.json()


def load_existing():
    """URLs and headline keys we've stored recently, so we don't re-score them."""
    cutoff = iso(now_utc() - timedelta(days=RETENTION_DAYS + 15))
    urls, titles, sets, start = set(), set(), [], 0
    while True:
        r = sb("GET", "news_items",
               params={"select": "url,title", "created_at": f"gte.{cutoff}", "order": "id"},
               extra_headers={"Range": f"{start}-{start + 999}"})
        rows = r.json()
        for row in rows:
            urls.add(row["url"])
            titles.add(title_key(row["title"]))
            sets.append(word_set(row["title"]))
        if len(rows) < 1000:
            break
        start += 1000
    return urls, titles, sets


def mark_source(src, ok, error=None):
    """Record feed health. Switches a feed off after MAX_FAILURES failures in a row."""
    if DRY_RUN:
        return
    patch = {"last_checked_at": iso(now_utc())}
    if ok:
        patch.update({"consecutive_failures": 0, "last_error": None})
    else:
        fails = (src.get("consecutive_failures") or 0) + 1
        patch.update({"consecutive_failures": fails, "last_error": str(error)[:300]})
        if fails >= MAX_FAILURES:
            patch["active"] = False
    try:
        sb("PATCH", "news_sources", params={"id": f"eq.{src['id']}"}, json_body=patch)
    except Exception as exc:
        print(f"  (could not update health for {src['name']}: {exc})")


def save_items(rows):
    for i in range(0, len(rows), 100):
        sb("POST", "news_items", params={"on_conflict": "url"},
           json_body=rows[i:i + 100],
           extra_headers={"Prefer": "resolution=ignore-duplicates,return=minimal"})


def delete_old():
    cutoff = iso(now_utc() - timedelta(days=RETENTION_DAYS))
    sb("DELETE", "news_items", params={"created_at": f"lt.{cutoff}"})


# ----------------------------------------------------------------------
# FEEDS
# ----------------------------------------------------------------------
def fetch_feed(src):
    r = requests.get(src["feed_url"], headers={"User-Agent": USER_AGENT}, timeout=FEED_TIMEOUT)
    r.raise_for_status()
    parsed = feedparser.parse(r.content)
    if not parsed.entries:
        raise ValueError("feed returned no articles")
    return parsed.entries[:MAX_ITEMS_PER_FEED]


# ----------------------------------------------------------------------
# GEMINI
# ----------------------------------------------------------------------
def object_array(properties):
    return {"type": "array", "items": {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}}

SCORE_SCHEMA = object_array({"i": {"type": "integer"}, "relevance": {"type": "integer"},
    **{key: {"type": "string"} for key in ("category", "region", "summary", "why_it_matters")}})
GROUP_SCHEMA = object_array({"id": {"type": "integer"}, "story": {"type": "string"}})
_generator = None

def gemini_json(prompt, schema=None):
    """Compatibility entry point; all news calls share provider and run budget."""
    global _generator
    if _generator is None:
        _generator = StructuredGenerator("NEWS", GEMINI_MODEL, GEMINI_TIMEOUT,
            thinking_level="" if THINKING_LEVEL == "off" else THINKING_LEVEL.lower(), temperature=0.1)
        print(f"LLM provider={_generator.provider} model={_generator.model}")
    try:
        return _generator.generate(prompt, schema or SCORE_SCHEMA)
    finally:
        metrics = _generator.metrics
        TOKENS.update({"in": metrics["prompt_tokens"], "out": metrics["output_tokens"],
                       "think": metrics["thinking_tokens"], "calls": metrics["api_attempts"]})

def gemini_score(batch):
    """batch: list of {"i", "title", "source", "snippet"}. Returns list of dicts."""
    lines = []
    for item in batch:
        parts = [str(item["i"]), item["source"], item["title"], item.get("snippet", "")]
        lines.append(" | ".join(p.replace("|", "/") for p in parts).rstrip(" |"))
    return gemini_json(PROMPT + "\n".join(lines))


# ----------------------------------------------------------------------
# STORY GROUPING (one card per story, other outlets listed underneath)
# ----------------------------------------------------------------------
def clean_key(key):
    key = re.sub(r"[^a-z0-9]+", "-", str(key).lower()).strip("-")
    return key[:60] or None


def official_source(row):
    return "gov" in (row.get("source_name") or "").lower()


def load_existing_stories():
    """Stories already showing in the feed (one row per story), so new articles
    about the same story are merged into them instead of appearing again."""
    cutoff = iso(now_utc() - timedelta(days=14))
    r = sb("GET", "news_items", params={
        "select": "story_key,title", "is_primary": "eq.true",
        "story_key": "not.is.null", "relevance": f"gte.{MIN_RELEVANCE}",
        "created_at": f"gte.{cutoff}", "order": "id.desc", "limit": "150"})
    return r.json()


def assign_stories(rows, existing):
    """Fills in story_key and is_primary on each kept row.
    Returns {story_key: {"members": [rows], "existing": bool}} for the report."""
    kept = [r for r in rows if r["relevance"] >= MIN_RELEVANCE][:MAX_GROUP_ITEMS]
    if not kept:
        return {}
    existing_keys = {e["story_key"] for e in existing}
    existing_lines = "\n".join(
        f"{e['story_key']} | {e['title'][:110].replace('|', '/')}" for e in existing) or "(none)"
    new_lines = "\n".join(
        f"{n} | {r['title'][:110].replace('|', '/')} | {r['source_name']}"
        for n, r in enumerate(kept))
    answer = gemini_json(GROUP_PROMPT.replace("{existing}", existing_lines)
                                     .replace("{new}", new_lines), GROUP_SCHEMA)
    keys = {}
    for item in answer:
        try:
            n, key = int(item["id"]), clean_key(item["story"])
        except Exception:
            continue
        if key and 0 <= n < len(kept):
            keys[n] = key

    groups = {}
    for n, r in enumerate(kept):
        if keys.get(n):
            groups.setdefault(keys[n], []).append(r)

    report = {}
    for key, members in groups.items():
        if key in existing_keys:
            # Story already has a card in the feed: these are extra outlets.
            for r in members:
                r["story_key"], r["is_primary"] = key, False
        else:
            # New story: the highest-scoring article (official sources win ties) gets the card.
            members.sort(key=lambda r: (-r["relevance"], 0 if official_source(r) else 1))
            for i, r in enumerate(members):
                r["story_key"], r["is_primary"] = key, (i == 0)
        report[key] = {"members": members, "existing": key in existing_keys}
    return report


# ----------------------------------------------------------------------
# SELF-TEST
# ----------------------------------------------------------------------
def self_test():
    problems = []
    for name in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", credential_name("NEWS")):
        if not os.environ.get(name):
            problems.append(f"missing setting: {name}")
    if problems:
        print("SELF-TEST FAILED:\n  " + "\n  ".join(problems))
        return 1
    try:
        sb("GET", "news_sources", params={"select": "id", "limit": "1"})
        print("Supabase: OK")
        try:
            sb("GET", "news_items", params={"select": "region", "limit": "1"})
            print("news_items.region column: OK")
        except Exception:
            problems.append("news_items has no 'region' column yet. Run the region SQL in Supabase first.")
        try:
            sb("GET", "news_items", params={"select": "story_key,is_primary", "limit": "1"})
            print("news_items story columns: OK")
        except Exception:
            problems.append("news_items has no 'story_key'/'is_primary' columns yet. Run story_grouping.sql in Supabase first.")
        try:
            sb("GET", "pipeline_runs", params={"select": "id", "limit": "1"})
            print("pipeline_runs table: OK")
        except Exception:
            problems.append("pipeline_runs table is missing. Run pipeline_runs.sql in Supabase first.")
    except Exception as exc:
        problems.append(f"Supabase: {exc}")
    try:
        result = gemini_score([{"i": 0, "title": "Changes to paternity leave rules announced",
                                "source": "test", "snippet": ""}])
        print(f"LLM ({selection('NEWS', GEMINI_MODEL)}): OK ({len(result)} result)")
    except Exception as exc:
        problems.append(f"LLM: {exc}")
    if TOKENS["calls"]:
        log_run({"scored": 0}, worker="news-selftest", dry_run=True)
    if problems:
        print("SELF-TEST FAILED:\n  " + "\n  ".join(problems))
        return 1
    print("SELF-TEST PASSED")
    return 0


# ----------------------------------------------------------------------
# RUN LOG (one row per run in the pipeline_runs table)
# ----------------------------------------------------------------------
def log_run(stats, worker="news", dry_run=None):
    skipped = sum(v for k, v in stats.items() if k.startswith("skipped_"))
    row = {
        "worker": worker,
        "dry_run": DRY_RUN if dry_run is None else dry_run,
        "input_tokens": TOKENS["in"],
        "output_tokens": TOKENS["out"],
        "gemini_calls": TOKENS["calls"],
        "articles_scored": stats["scored"],
        "skipped_prefilter": skipped,
    }
    try:
        sb("POST", "pipeline_runs", json_body=row,
           extra_headers={"Prefer": "return=minimal"})
        print("Run logged to pipeline_runs.")
    except Exception as exc:  # logging must never break the run
        print(f"(could not log this run: {exc})")


# ----------------------------------------------------------------------
# MAIN RUN
# ----------------------------------------------------------------------
def run():
    stats = {"sources_ok": 0, "sources_failed": 0, "new_articles": 0,
             "scored": 0, "kept": 0, "low_relevance": 0,
             "saved": 0, "batches_failed": 0,
             "duplicates_merged": 0, "stories_shown": 0,
             "skipped_blocked_word": 0, "skipped_no_family_word": 0,
             "skipped_near_duplicate": 0}
    failed_sources = []
    kept_lines, rejected_lines = [], []
    per_source = {}  # feed name -> [scored, kept]
    skipped_lines = []  # what the free pre-filter removed (shown in dry run)
    story_lines = []  # duplicate stories that were merged (shown in dry run)
    all_rows = []  # every scored article, saved together after grouping

    print(f"Dadspace news worker | dry_run={DRY_RUN} | provider/model={selection('NEWS', GEMINI_MODEL)} | Gemini thinking={THINKING_LEVEL}")

    try:
        sources = load_sources()
        print(f"Active sources: {len(sources)}")
        seen_urls, seen_titles, known_sets = load_existing()

        # ---- 1) collect new articles from every feed
        candidates = []
        for src in sources:
            if out_of_time() or len(candidates) >= MAX_NEW_PER_RUN:
                print("Stopping collection early (time or article limit reached).")
                break
            t0 = time.time()
            try:
                entries = fetch_feed(src)
            except Exception as exc:
                stats["sources_failed"] += 1
                failed_sources.append(f"{src['name']}: {str(exc)[:100]}")
                mark_source(src, ok=False, error=exc)
                print(f"  FAIL  {src['name']}: {str(exc)[:100]}")
                continue

            mark_source(src, ok=True)
            stats["sources_ok"] += 1
            added = too_old = already = 0
            for e in entries:
                title = clean_text(e.get("title"), 300)
                link = clean_url(e.get("link", "")) if e.get("link") else ""
                if not title or not link:
                    continue
                published = entry_date(e)
                if published and published < now_utc() - timedelta(days=MAX_ARTICLE_AGE_DAYS):
                    too_old += 1
                    continue
                key = title_key(title)
                if link in seen_urls or key in seen_titles:
                    already += 1
                    continue
                seen_urls.add(link)
                seen_titles.add(key)
                publisher = (e.get("source") or {}).get("title") or src["name"]

                # Snippet: short, and dropped when it only repeats the headline
                # (Google News snippets are just the headline again = wasted tokens).
                snippet = clean_text(e.get("summary"), SNIPPET_CHARS)
                if "news.google.com" in src["feed_url"] or title_key(title)[:30] in title_key(snippet):
                    snippet = ""

                # Free checks before spending any Gemini tokens
                reason = prefilter(title, snippet, src.get("filter_mode") or "none")
                if reason:
                    stats[f"skipped_{reason}"] += 1
                    skipped_lines.append(f"({reason}) {title}  [{publisher}]")
                    continue
                words = word_set(title)
                if is_near_duplicate(words, known_sets):
                    stats["skipped_near_duplicate"] += 1
                    skipped_lines.append(f"(near_duplicate) {title}  [{publisher}]")
                    continue
                known_sets.append(words)

                candidates.append({
                    "src": src, "title": title, "url": link, "published": published,
                    "publisher": publisher, "snippet": snippet,
                })
                added += 1
            print(f"  ok    {src['name']}: {added} new, {len(entries)} in feed, "
                  f"{too_old} too old, {already} already seen ({time.time() - t0:.1f}s)")

        stats["new_articles"] = len(candidates)
        print(f"New articles to score: {len(candidates)}")

        # ---- 2) score with Gemini in batches, then save
        for start in range(0, len(candidates), BATCH_SIZE):
            if out_of_time():
                print("Stopping scoring early (time limit reached).")
                break
            chunk = candidates[start:start + BATCH_SIZE]
            payload = [{"i": n, "title": c["title"], "source": c["publisher"],
                        "snippet": c["snippet"]} for n, c in enumerate(chunk)]
            try:
                results = gemini_score(payload)
            except (FatalLLMError, BudgetExhausted):
                raise
            except Exception as exc:
                stats["batches_failed"] += 1
                print(f"  Batch failed (will retry next run): {exc}")
                continue

            rows = []
            for res in results:
                try:
                    c = chunk[int(res["i"])]
                    relevance = max(0, min(5, int(res.get("relevance", 0))))
                except Exception:
                    continue
                category = res.get("category") if res.get("category") in CATEGORIES else "other"
                region = str(res.get("region", "uk")).strip().lower().replace(" ", "_")
                if region not in REGIONS:
                    region = "uk"
                summary = clean_text(res.get("summary"), 300)
                why = clean_text(res.get("why_it_matters"), 150)
                stats["scored"] += 1
                counts = per_source.setdefault(c["src"]["name"], [0, 0])
                counts[0] += 1
                line = f"[{relevance}] ({region}) {c['title']}  ({c['publisher']})"
                if relevance >= MIN_RELEVANCE:
                    counts[1] += 1
                    stats["kept"] += 1
                    kept_lines.append(f"{line}\n      -> {why}")
                else:
                    stats["low_relevance"] += 1
                    rejected_lines.append(line)
                rows.append({
                    "source_id": c["src"]["id"], "source_name": c["publisher"],
                    "title": c["title"], "url": c["url"],
                    "published_at": iso(c["published"]) if c["published"] else None,
                    "summary": summary, "why_it_matters": why,
                    "category": category, "relevance": relevance,
                    "region": region,
                })
            all_rows.extend(rows)

        # ---- 2b) group articles that are the same story
        for r in all_rows:
            r["story_key"], r["is_primary"] = None, True
        if all_rows and not out_of_time():
            try:
                story_groups = assign_stories(all_rows, load_existing_stories())
                stats["duplicates_merged"] = sum(1 for r in all_rows if not r["is_primary"])
                for key, info in story_groups.items():
                    members = info["members"]
                    if len(members) < 2 and not info["existing"]:
                        continue
                    tag = " [already in feed]" if info["existing"] else ""
                    story_lines.append(f"{key} ({len(members)} articles){tag}")
                    for r in members:
                        mark = "SHOWN " if r["is_primary"] else "merged"
                        story_lines.append(f"    {mark} [{r['relevance']}] {r['title'][:100]}  ({r['source_name']})")
            except Exception as exc:
                print(f"  Story grouping failed, saving without grouping: {exc}")
                for r in all_rows:
                    r["story_key"], r["is_primary"] = None, True
        stats["stories_shown"] = stats["kept"] - stats["duplicates_merged"]

        # Resolve only relevant articles, after scoring and grouping.
        kept = [row for row in all_rows if row["relevance"] >= MIN_RELEVANCE]
        destinations = resolve_article_urls([row["url"] for row in kept])
        for row, destination in zip(kept, destinations):
            row["url"] = clean_url(destination)

        if all_rows and not DRY_RUN:
            save_items(all_rows)
            stats["saved"] = len(all_rows)

        # ---- 3) tidy up
        if not DRY_RUN:
            delete_old()

    except (FatalLLMError, BudgetExhausted) as exc:
        print(f"LLM run stopped: {exc}")
        raise
    except Exception:
        print("UNEXPECTED ERROR:")
        traceback.print_exc()
    finally:
        print("\n" + "=" * 60)
        if DRY_RUN:
            print("DRY RUN: nothing was saved.")
            print(f"\nWould KEEP ({len(kept_lines)}):")
            for line in kept_lines[:200]:
                print("  " + line)
            # Spread the rejected sample evenly so every source is represented
            step = max(1, len(rejected_lines) // 40)
            sample = rejected_lines[::step][:40]
            print(f"\nSample of REJECTED ({len(rejected_lines)} total, showing {len(sample)}):")
            for line in sample:
                print("  " + line)
        if DRY_RUN and story_lines:
            print(f"\nSTORY GROUPS: same story from several outlets ({stats['duplicates_merged']} "
                  f"merged, so the feed would show {stats['stories_shown']} cards):")
            for line in story_lines:
                print("  " + line)
        if DRY_RUN and skipped_lines:
            step = max(1, len(skipped_lines) // 40)
            print(f"\nSKIPPED BEFORE GEMINI, free ({len(skipped_lines)} total, "
                  f"showing {len(skipped_lines[::step][:40])}). Check nothing good is in here:")
            for line in skipped_lines[::step][:40]:
                print("  " + line)
        print("\nPER-SOURCE RESULTS (kept / scored)")
        for name, (scored, kept) in per_source.items():
            print(f"  {kept:>3} / {scored:<3}  {name}")
        print("\nSUMMARY")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        print(f"  gemini_calls: {TOKENS['calls']}")
        print(f"  input_tokens: {TOKENS['in']:,}")
        print(f"  output_tokens: {TOKENS['out']:,}  (of which thinking: {TOKENS['think']:,})")
        print(f"  thinking_level: {THINKING_LEVEL}")
        if failed_sources:
            print("  failing feeds:")
            for f in failed_sources:
                print("    - " + f)
        print(f"  minutes: {(time.time() - START) / 60:.1f}")
        print("=" * 60)
        log_run(stats)
        if _generator is not None:
            print("LLM usage: " + json.dumps(_generator.metrics, sort_keys=True))
            _generator.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY and os.getenv(credential_name("NEWS"))):
        print("Missing Supabase credentials or selected LLM API key")
        sys.exit(1)
    run()

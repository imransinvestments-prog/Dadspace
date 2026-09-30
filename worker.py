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

DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() != "false"
MIN_RELEVANCE = int(os.environ.get("MIN_RELEVANCE", "3"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "20"))
MAX_ITEMS_PER_FEED = int(os.environ.get("MAX_ITEMS_PER_FEED", "30"))
MAX_NEW_PER_RUN = int(os.environ.get("MAX_NEW_PER_RUN", "300"))
MAX_ARTICLE_AGE_DAYS = int(os.environ.get("MAX_ARTICLE_AGE_DAYS", "14"))
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))
MAX_FAILURES = int(os.environ.get("MAX_FAILURES", "5"))
MAX_RUN_MINUTES = int(os.environ.get("MAX_RUN_MINUTES", "20"))
FEED_TIMEOUT = 15
GEMINI_TIMEOUT = 60

USER_AGENT = "Mozilla/5.0 (compatible; DadspaceNewsBot/1.0)"
CATEGORIES = ["policy", "money", "health", "safety", "activities",
              "parenting", "wellbeing", "education", "other"]

PROMPT = """You are the editor of Dadspace, a UK app for fathers of children aged 0-16.
For each article below, decide how useful it is to a UK dad.

Score "relevance" from 0 to 5:
5 = directly about dads or fatherhood, or a UK rule, benefit, deadline, recall or event that families need to act on
4 = clearly useful to UK parents (childcare, school, health, money, safety, days out)
3 = useful to some parents and has a real family angle
2 = tangential
1 = barely connected
0 = not relevant (celebrity gossip, sport results, adult-only topics, overseas-only news, adverts or sponsored posts, politics with no family angle)

Also give:
- "category": one of policy, money, health, safety, activities, parenting, wellbeing, education, other
- "summary": one plain sentence (max 25 words) in your own words
- "why_it_matters": max 15 words, written for a dad

Reply with ONLY a JSON array, one object per article, like:
[{"i": 0, "relevance": 4, "category": "money", "summary": "...", "why_it_matters": "..."}]

Articles:
"""

START = time.time()


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
    urls, titles, start = set(), set(), 0
    while True:
        r = sb("GET", "news_items",
               params={"select": "url,title", "created_at": f"gte.{cutoff}", "order": "id"},
               extra_headers={"Range": f"{start}-{start + 999}"})
        rows = r.json()
        for row in rows:
            urls.add(row["url"])
            titles.add(title_key(row["title"]))
        if len(rows) < 1000:
            break
        start += 1000
    return urls, titles


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
def gemini_score(batch):
    """batch: list of {"i", "title", "source", "snippet"}. Returns list of dicts."""
    body = {
        "contents": [{"parts": [{"text": PROMPT + json.dumps(batch, ensure_ascii=False)}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    last_error = None
    for attempt in range(2):
        try:
            r = requests.post(url, headers={"x-goog-api-key": GEMINI_API_KEY},
                              json=body, timeout=GEMINI_TIMEOUT)
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
            if isinstance(data, dict):
                data = data.get("articles") or data.get("results") or [data]
            return data
        except Exception as exc:
            last_error = exc
            time.sleep(3)
    raise RuntimeError(f"Gemini failed: {last_error}")


# ----------------------------------------------------------------------
# SELF-TEST
# ----------------------------------------------------------------------
def self_test():
    problems = []
    for name in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "GEMINI_API_KEY"):
        if not os.environ.get(name):
            problems.append(f"missing setting: {name}")
    if problems:
        print("SELF-TEST FAILED:\n  " + "\n  ".join(problems))
        return 1
    try:
        sb("GET", "news_sources", params={"select": "id", "limit": "1"})
        print("Supabase: OK")
    except Exception as exc:
        problems.append(f"Supabase: {exc}")
    try:
        result = gemini_score([{"i": 0, "title": "Changes to paternity leave rules announced",
                                "source": "test", "snippet": ""}])
        print(f"Gemini ({GEMINI_MODEL}): OK ({len(result)} result)")
    except Exception as exc:
        problems.append(f"Gemini: {exc}")
        try:
            r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                             headers={"x-goog-api-key": GEMINI_API_KEY},
                             params={"pageSize": 100}, timeout=30)
            names = [m["name"].replace("models/", "") for m in r.json().get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])
                     and "flash" in m["name"]]
            print("Flash models your key can use right now:\n  " + "\n  ".join(names))
        except Exception as exc2:
            print(f"(could not list models: {exc2})")
    if problems:
        print("SELF-TEST FAILED:\n  " + "\n  ".join(problems))
        return 1
    print("SELF-TEST PASSED")
    return 0


# ----------------------------------------------------------------------
# MAIN RUN
# ----------------------------------------------------------------------
def run():
    stats = {"sources_ok": 0, "sources_failed": 0, "new_articles": 0,
             "scored": 0, "kept": 0, "low_relevance": 0,
             "saved": 0, "batches_failed": 0}
    failed_sources = []
    kept_lines, rejected_lines = [], []

    print(f"Dadspace news worker | dry_run={DRY_RUN} | model={GEMINI_MODEL}")

    try:
        sources = load_sources()
        print(f"Active sources: {len(sources)}")
        seen_urls, seen_titles = load_existing()

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
            added = 0
            for e in entries:
                title = clean_text(e.get("title"), 300)
                link = clean_url(e.get("link", "")) if e.get("link") else ""
                if not title or not link:
                    continue
                published = entry_date(e)
                if published and published < now_utc() - timedelta(days=MAX_ARTICLE_AGE_DAYS):
                    continue
                key = title_key(title)
                if link in seen_urls or key in seen_titles:
                    continue
                seen_urls.add(link)
                seen_titles.add(key)
                publisher = (e.get("source") or {}).get("title") or src["name"]
                candidates.append({
                    "src": src, "title": title, "url": link, "published": published,
                    "publisher": publisher, "snippet": clean_text(e.get("summary"), 300),
                })
                added += 1
            print(f"  ok    {src['name']}: {added} new ({time.time() - t0:.1f}s)")

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
                summary = clean_text(res.get("summary"), 300)
                why = clean_text(res.get("why_it_matters"), 150)
                stats["scored"] += 1
                line = f"[{relevance}] {c['title']}  ({c['publisher']})"
                if relevance >= MIN_RELEVANCE:
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
                })
            if rows and not DRY_RUN:
                save_items(rows)
                stats["saved"] += len(rows)

        # ---- 3) tidy up
        if not DRY_RUN:
            delete_old()

    except Exception:
        print("UNEXPECTED ERROR:")
        traceback.print_exc()
    finally:
        print("\n" + "=" * 60)
        if DRY_RUN:
            print("DRY RUN: nothing was saved.")
            print(f"\nWould KEEP ({len(kept_lines)}):")
            for line in kept_lines[:40]:
                print("  " + line)
            print(f"\nSample of REJECTED ({len(rejected_lines)} total):")
            for line in rejected_lines[:15]:
                print("  " + line)
        print("\nSUMMARY")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        if failed_sources:
            print("  failing feeds:")
            for f in failed_sources:
                print("    - " + f)
        print(f"  minutes: {(time.time() - START) / 60:.1f}")
        print("=" * 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if not (SUPABASE_URL and SUPABASE_SERVICE_KEY and GEMINI_API_KEY):
        print("Missing SUPABASE_URL, SUPABASE_SERVICE_KEY or GEMINI_API_KEY")
        sys.exit(1)
    run()

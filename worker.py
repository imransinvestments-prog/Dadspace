"""
Family events collector.

What it does, in plain English:
  1. Reads the list of websites from the Supabase `sources` table (only rows where active = true).
  2. Downloads each page and turns it into plain text.
  3. Asks Google Gemini to pull out the events (title, date, place, cost...).
  4. Throws away anything with no date, anything in the past, and anything not family-relevant.
  5. Saves what is left into the Supabase `collected_events` table (updating events it has seen before).

You do not run this on your own computer. GitHub runs it for you (see collect.yml).
Settings come from "secrets" and options set in GitHub, never from this file.
"""

import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from urllib import robotparser
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------------
# Settings (all can be changed from GitHub without editing this file)
# ----------------------------------------------------------------------------
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-3.6-flash"   # can be changed from GitHub without editing this file
EVENTS_TABLE = os.environ.get("EVENTS_TABLE", "collected_events")  # where events are saved
LIMIT = int(os.environ.get("LIMIT", "0") or 0)              # 0 = every active source
DRY_RUN = os.environ.get("DRY_RUN", "false").strip().lower() == "true"
MIN_RELEVANCE = int(os.environ.get("MIN_RELEVANCE", "2"))   # 1-5; events scoring lower are dropped
MAX_CHARS = int(os.environ.get("MAX_CHARS", "40000"))       # how much page text to send to Gemini
PAUSE_SECONDS = float(os.environ.get("PAUSE_SECONDS", "2")) # politeness delay between websites
USER_AGENT = "Mozilla/5.0 (compatible; FamilyEventsBot/0.1)"
TIMEZONE = ZoneInfo("Europe/London")

EVENT_FIELDS = [
    "title", "description", "start_date", "end_date", "time_text", "location",
    "event_url", "cost_text", "age_range", "recurrence", "family_relevance", "confidence",
]


class FatalError(Exception):
    """A problem that will affect every website (wrong model name, bad key), so the run should stop."""


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def today_uk():
    return dt.datetime.now(TIMEZONE).date()


def parse_date(value):
    """Turn '2026-10-03' (or '2026-10-03T10:00:00') into a date, or None."""
    if not value or not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def clean_str(value, max_len):
    if value is None:
        return None
    text = str(value).strip()
    return text[:max_len] if text else None


def make_dedupe_key(source_id, title, start_date, location):
    """Same source + title + date + place = same event, so re-runs update instead of duplicating."""
    raw = "|".join([
        str(source_id),
        re.sub(r"\s+", " ", (title or "").lower()).strip(),
        str(start_date),
        re.sub(r"\s+", " ", (location or "").lower()).strip(),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------
# Fetching pages
# ----------------------------------------------------------------------------
def robots_allows(url):
    """Respect the website's robots.txt. Returns (allowed, reason)."""
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        resp = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=15)
    except requests.RequestException:
        return True, ""  # can't read it; the page fetch itself will fail if the site is down
    if resp.status_code >= 500:
        return False, "robots.txt returned a server error"
    if resp.status_code != 200:
        return True, ""  # no robots.txt = no restrictions
    parser = robotparser.RobotFileParser()
    parser.parse(resp.text.splitlines())
    if parser.can_fetch(USER_AGENT, url):
        return True, ""
    return False, "robots.txt does not allow this page"


def fetch_html(url):
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.text


def _walk(node):
    """Yield every dict found anywhere inside parsed JSON."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def extract_jsonld_events(soup):
    """Many sites embed machine-readable events (schema.org). If present, use them."""
    found = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or tag.get_text() or "")
        except (ValueError, TypeError):
            continue
        for item in _walk(data):
            types = item.get("@type")
            types = types if isinstance(types, list) else [types]
            if any(isinstance(t, str) and t.endswith("Event") for t in types):
                found.append(item)
    return found


def page_to_text(soup, base_url):
    """Strip menus/scripts and keep readable text, with link addresses next to link text."""
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "form", "nav", "footer"]):
        tag.decompose()
    for link in soup.find_all("a", href=True):
        label = link.get_text(" ", strip=True)
        if label:
            link.replace_with(f"{label} [{urljoin(base_url, link['href'])}]")
    text = soup.get_text("\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def prepare_content(html, url):
    """Return (content_for_gemini, method_label)."""
    soup = BeautifulSoup(html, "html.parser")
    events = extract_jsonld_events(soup)  # must happen before page_to_text removes scripts
    if events:
        return json.dumps(events, ensure_ascii=False)[:MAX_CHARS], "jsonld+llm"
    return page_to_text(soup, url)[:MAX_CHARS], "llm"


# ----------------------------------------------------------------------------
# Gemini
# ----------------------------------------------------------------------------
def build_prompt(source, url, content, today):
    return f"""You extract public events from a web page for a UK database of things for parents, dads and families to do with children.

Today's date is {today.isoformat()} (UK). The page is from "{source['name']}" ({url}).

Return a JSON list of events found in the content below. Rules:
- Only include real, specific events, open days or attractions with a date. Never invent details. If the content has no events, return an empty list.
- Dates must be ISO format YYYY-MM-DD. Work out relative dates ("this Saturday", "next month") from today's date. If an event has no clear date, leave start_date null.
- For multi-day events set start_date and end_date. For a single day, end_date can equal start_date.
- Skip council committee meetings, adult-only events, job adverts, and things that are only for sale.
- family_relevance is 1-5: 5 = clearly designed for children/families, 3 = suitable for families or a good day out for a parent with kids, 1 = not relevant to families.
- Rate niche interests highly when children could enjoy them: steam days, heritage transport, engineering museums and depots, boat trips, farms, open days.
- event_url should be the link for that specific event if one appears in the content (links appear as [url] after the link text).
- recurrence is one of: one_off, recurring, seasonal, unknown.
- confidence is 0-1: how sure you are the details are correct and come from the content.

CONTENT:
{content}
"""


def make_gemini_caller():
    """Set up the Gemini client. The libraries are imported here so the rest of the file can be tested without them."""
    from google import genai
    from google.genai import types
    from pydantic import BaseModel
    from typing import Optional

    class EventSchema(BaseModel):
        title: str
        description: Optional[str]
        start_date: Optional[str]
        end_date: Optional[str]
        time_text: Optional[str]
        location: Optional[str]
        event_url: Optional[str]
        cost_text: Optional[str]
        age_range: Optional[str]
        recurrence: Optional[str]
        family_relevance: int
        confidence: float

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def call(prompt):
        last_error = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=list[EventSchema],
                        temperature=0,
                    ),
                )
                data = json.loads(response.text)
                if not isinstance(data, list):
                    raise ValueError("Gemini did not return a list")
                return data
            except Exception as exc:  # retry on any temporary problem
                text = str(exc)
                if any(word in text for word in ("NOT_FOUND", "PERMISSION_DENIED", "UNAUTHENTICATED", "API key not valid")):
                    raise FatalError(
                        f"Gemini rejected the request ({text[:300]}). "
                        "The model name may be retired (change the GEMINI_MODEL variable in GitHub) "
                        "or the GEMINI_API_KEY secret may be wrong."
                    )
                last_error = exc
                time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"Gemini failed after 3 tries: {last_error}")

    return call


def clean_events(raw_events, source, page_url, method, today):
    """Validate what Gemini returned and turn it into database rows."""
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    rows = {}
    for item in raw_events:
        if not isinstance(item, dict):
            continue
        title = clean_str(item.get("title"), 300)
        start = parse_date(item.get("start_date"))
        if not title or not start:
            continue                      # no date = not useful
        end = parse_date(item.get("end_date")) or start
        if end < start:
            end = start
        if end < today:
            continue                      # already finished
        try:
            relevance = int(item.get("family_relevance") or 0)
        except (TypeError, ValueError):
            relevance = 0
        if relevance < MIN_RELEVANCE:
            continue
        try:
            confidence = float(item.get("confidence") or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        location = clean_str(item.get("location"), 300)
        event_url = clean_str(item.get("event_url"), 500)
        if event_url:
            event_url = urljoin(page_url, event_url)
        key = make_dedupe_key(source["id"], title, start, location)
        new_row = {
            "source_id": source["id"],
            "title": title,
            "description": clean_str(item.get("description"), 1000),
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "time_text": clean_str(item.get("time_text"), 200),
            "location": location,
            "event_url": event_url,
            "cost_text": clean_str(item.get("cost_text"), 200),
            "age_range": clean_str(item.get("age_range"), 100),
            "recurrence": clean_str(item.get("recurrence"), 30),
            "family_relevance": max(1, min(5, relevance)),
            "confidence": max(0.0, min(1.0, confidence)),
            "source_url": page_url,
            "extraction_method": method,
            "dedupe_key": key,
            "last_verified_at": now_iso,
        }
        if key in rows:
            # Same event listed twice on one page: keep the first, fill any gaps from the second
            for field, value in new_row.items():
                if rows[key].get(field) is None and value is not None:
                    rows[key][field] = value
        else:
            rows[key] = new_row
    return list(rows.values())


# ----------------------------------------------------------------------------
# Processing one source
# ----------------------------------------------------------------------------
def process_source(source, extract, today):
    """Returns (status, event_rows, new_hash, message)."""
    url = source["url"]
    allowed, reason = robots_allows(url)
    if not allowed:
        return "skipped", [], None, reason
    html = fetch_html(url)
    content, method = prepare_content(html, url)
    if len(content) < 200:
        return "failed", [], None, "Page had almost no readable text (it may need a browser to load its events)"
    new_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if new_hash == source.get("last_hash") and source.get("last_success_at"):
        return "unchanged", [], new_hash, "Page unchanged since last run"
    raw = extract(build_prompt(source, url, content, today))
    rows = clean_events(raw, source, url, method, today)
    return "ok", rows, new_hash, f"{len(raw)} found by Gemini, {len(rows)} kept"


def main():
    missing = [n for n in ("SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY") if not os.environ.get(n)]
    if missing:
        print("Setup problem: these GitHub secrets are missing or empty: " + ", ".join(missing))
        sys.exit(1)

    # Tidy up the secrets: remove stray spaces, line breaks and quote marks from copy-and-paste
    supabase_url = os.environ["SUPABASE_URL"].strip().strip("\"'").rstrip("/")
    supabase_key = os.environ["SUPABASE_KEY"].strip().strip("\"'")
    if not re.fullmatch(r"https://[A-Za-z0-9-]+\.supabase\.co", supabase_url):
        print("Setup problem: the SUPABASE_URL secret does not look right.")
        print("It should look like  https://abcdefghijklmnop.supabase.co  (starts with https://, ends with .supabase.co, nothing after it).")
        print(f"What the worker received starts with: {supabase_url[:8]!r} and is {len(supabase_url)} characters long.")
        sys.exit(1)

    from supabase import create_client
    db = create_client(supabase_url, supabase_key)
    extract = make_gemini_caller()
    today = today_uk()

    sources = db.table("sources").select("*").eq("active", True).execute().data
    # Never-checked sources first, then the ones checked longest ago
    sources.sort(key=lambda s: s.get("last_checked_at") or "")
    if LIMIT > 0:
        sources = sources[:LIMIT]

    print(f"Today (UK): {today}. Sources to process: {len(sources)}. Dry run: {DRY_RUN}. Model: {MODEL}")
    totals = {"ok": 0, "unchanged": 0, "skipped": 0, "failed": 0}
    total_events = 0
    zero_event_sources = []

    for number, source in enumerate(sources, start=1):
        label = f"[{number}/{len(sources)}] {source['name']}"
        now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
        update = {"last_checked_at": now_iso}
        try:
            status, rows, new_hash, message = process_source(source, extract, today)
        except FatalError as exc:
            print(f"{label}: STOPPING THE WHOLE RUN - {exc}")
            sys.exit(1)
        except Exception as exc:
            status, rows, new_hash, message = "failed", [], None, f"{type(exc).__name__}: {exc}"

        totals[status] += 1
        print(f"{label}: {status.upper()} - {message}")

        if status == "ok":
            update.update({"last_hash": new_hash, "last_success_at": now_iso, "fail_count": 0,
                           "last_error": None, "last_event_count": len(rows)})
            total_events += len(rows)
            if not rows:
                zero_event_sources.append(source["name"])
            if rows and not DRY_RUN:
                db.table(EVENTS_TABLE).upsert(rows, on_conflict="dedupe_key").execute()
            if DRY_RUN:
                for row in rows[:5]:
                    print(f"      would save: {row['start_date']} | {row['title']} | {row['location']}")
        elif status == "unchanged":
            update.update({"fail_count": 0, "last_error": None})
        else:
            update.update({"fail_count": (source.get("fail_count") or 0) + 1, "last_error": message[:500]})

        if not DRY_RUN:
            db.table("sources").update(update).eq("id", source["id"]).execute()
        time.sleep(PAUSE_SECONDS)

    print("\n=== Summary ===")
    print(f"Saved/updated events: {total_events}{' (dry run - nothing was saved)' if DRY_RUN else ''}")
    print("Sources: " + ", ".join(f"{k}={v}" for k, v in totals.items()))
    if zero_event_sources:
        print("Worked but found 0 events (worth a look): " + "; ".join(zero_event_sources))


if __name__ == "__main__":
    main()

"""
Dadspace family events collector - requests track.

Designed to be used by the GitHub Actions "reliable" workflow.
Browser/Playwright collection remains a separate workflow.

Main improvements:
- requests.Session + retries for transient HTTP failures
- clearer source status/error classification
- JSON-LD is combined with visible page text instead of replacing it
- strict future-date validation
- configurable future window
- event-level validation and rejection counters
- better URL handling
- safer robots.txt handling
- zero-event sources are reported separately
- page hashes are retained for diagnostics but do not prevent validation
- same Supabase tables/columns as the original worker
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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-3.6-flash"
FETCH_ENGINE = os.environ.get("FETCH_ENGINE", "requests").strip().lower()
CATEGORY_FILTER = [
    c.strip()
    for c in os.environ.get("CATEGORIES", "").split(",")
    if c.strip()
]
EVENTS_TABLE = os.environ.get("EVENTS_TABLE", "collected_events")
LIMIT = int(os.environ.get("LIMIT", "0") or 0)
DRY_RUN = os.environ.get("DRY_RUN", "false").strip().lower() == "true"

MIN_RELEVANCE = int(os.environ.get("MIN_RELEVANCE", "2"))
MIN_CONFIDENCE = float(os.environ.get("MIN_CONFIDENCE", "0.0"))

MAX_CHARS = int(os.environ.get("MAX_CHARS", "40000"))
MAX_JSONLD_CHARS = int(os.environ.get("MAX_JSONLD_CHARS", "12000"))

PAUSE_SECONDS = float(os.environ.get("PAUSE_SECONDS", "2"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "2"))

# Current/future events only. Default: today through one year ahead.
MIN_EVENT_DAYS_FROM_TODAY = int(
    os.environ.get("MIN_EVENT_DAYS_FROM_TODAY", "0")
)
MAX_EVENT_DAYS_FROM_TODAY = int(
    os.environ.get("MAX_EVENT_DAYS_FROM_TODAY", "365")
)

USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (compatible; DadspaceEventsBot/1.0)",
)
TIMEZONE = ZoneInfo("Europe/London")


class FatalError(Exception):
    """A problem that affects the whole run, not one source."""


# ----------------------------------------------------------------------------
# HTTP session
# ----------------------------------------------------------------------------
def make_http_session():
    retry = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        status=MAX_RETRIES,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )

    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    })
    return session


HTTP = make_http_session()


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def today_uk():
    return dt.datetime.now(TIMEZONE).date()


def parse_date(value):
    """Turn an ISO-like date into a date, or None."""
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


def normalise_text(value):
    return re.sub(r"\s+", " ", (value or "").lower()).strip()


def make_dedupe_key(title, start_date, location):
    raw = "|".join([
        normalise_text(title),
        str(start_date),
        normalise_text(location),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def absolute_url(value, base_url):
    if not value:
        return None
    try:
        result = urljoin(base_url, str(value).strip())
        parsed = urlparse(result)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return result
    except Exception:
        pass
    return None


def classify_http_status(status_code):
    if status_code == 404:
        return "http_404"
    if status_code in (401, 403):
        return "http_403"
    if status_code == 429:
        return "http_429"
    if 500 <= status_code <= 599:
        return "http_5xx"
    if 200 <= status_code <= 299:
        return "success"
    return f"http_{status_code}"


# ----------------------------------------------------------------------------
# Robots
# ----------------------------------------------------------------------------
def robots_allows(url):
    """Respect robots.txt. A temporary robots failure should not become a
    permanent source failure; the page fetch will still determine health."""
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"

    try:
        resp = HTTP.get(robots_url, timeout=15)
    except requests.RequestException:
        return True, ""

    # A server-side robots error is treated as unknown, not a block.
    if resp.status_code >= 500:
        return True, ""

    # Missing robots.txt means there are no robots rules to parse.
    if resp.status_code == 404:
        return True, ""

    if resp.status_code != 200:
        return True, ""

    parser = robotparser.RobotFileParser()
    parser.parse(resp.text.splitlines())

    if parser.can_fetch(USER_AGENT, url):
        return True, ""

    return False, "robots.txt does not allow this page"


# ----------------------------------------------------------------------------
# Fetching
# ----------------------------------------------------------------------------
def fetch_html_requests(url):
    """Fast requests-only fetch for this workflow."""
    try:
        resp = HTTP.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    except requests.Timeout as exc:
        raise RuntimeError(f"timeout after {REQUEST_TIMEOUT}s: {exc}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"request error: {exc}") from exc

    status = classify_http_status(resp.status_code)

    if status != "success":
        raise RuntimeError(
            f"{status}: {resp.url or url}"
        )

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if content_type and not any(
        t in content_type
        for t in ("text/html", "application/xhtml+xml", "application/json")
    ):
        raise RuntimeError(
            f"unexpected content type {content_type}"
        )

    if not resp.text.strip():
        raise RuntimeError("empty response body")

    return resp.text


def fetch_html(url):
    if FETCH_ENGINE != "requests":
        raise FatalError(
            f"This worker is the requests track, but FETCH_ENGINE={FETCH_ENGINE!r}. "
            "Use the separate browser workflow for browser collection."
        )
    return fetch_html_requests(url)


# ----------------------------------------------------------------------------
# Content extraction
# ----------------------------------------------------------------------------
def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def extract_jsonld_events(soup):
    """Extract schema.org Event objects when present."""
    found = []

    for tag in soup.find_all("script", type="application/ld+json"):
        raw = tag.string or tag.get_text() or ""
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue

        for item in _walk(data):
            types = item.get("@type")
            types = types if isinstance(types, list) else [types]

            if any(
                isinstance(t, str) and t.lower().endswith("event")
                for t in types
            ):
                found.append(item)

    return found


def page_to_text(soup, base_url):
    """Turn visible page content into compact text while preserving links."""
    for tag in soup(
        ["script", "style", "noscript", "svg", "iframe", "form", "nav", "footer"]
    ):
        tag.decompose()

    for link in soup.find_all("a", href=True):
        label = link.get_text(" ", strip=True)
        href = absolute_url(link["href"], base_url)

        if label and href:
            link.replace_with(f"{label} [{href}]")

    text = soup.get_text("\n")
    lines = [
        re.sub(r"[ \t]+", " ", line).strip()
        for line in text.splitlines()
    ]

    return "\n".join(line for line in lines if line)


def prepare_content(html, url):
    """
    Return content for Gemini.

    Important: JSON-LD does NOT replace visible text. Some sites have only
    some events in schema.org markup while additional events are visible
    elsewhere on the page.
    """
    soup = BeautifulSoup(html, "html.parser")
    events = extract_jsonld_events(soup)

    visible_text = page_to_text(soup, url)

    parts = []

    if events:
        jsonld_text = json.dumps(
            events,
            ensure_ascii=False,
        )

        parts.append(
            "STRUCTURED EVENT DATA (schema.org JSON-LD):\n"
            + jsonld_text[:MAX_JSONLD_CHARS]
        )

    if visible_text:
        remaining = max(0, MAX_CHARS - sum(len(p) for p in parts))
        if remaining:
            parts.append(
                "VISIBLE PAGE TEXT:\n"
                + visible_text[:remaining]
            )

    content = "\n\n".join(parts)
    method = "jsonld+llm" if events else "llm"

    return content[:MAX_CHARS], method


# ----------------------------------------------------------------------------
# Gemini
# ----------------------------------------------------------------------------
def build_prompt(source, url, content, today):
    return f"""You extract public events from a web page for Dadspace, a UK
database of things for parents, dads and families to do with children.

Today's date is {today.isoformat()} (UK).
The page is from "{source['name']}" ({url}).

Return a JSON list of events found in the supplied content.

IMPORTANT RULES:
- Only include real, specific events, open days, activities or attractions.
- Do not invent details.
- Only use dates supported by the supplied content.
- Dates must be ISO format YYYY-MM-DD.
- Resolve relative dates such as "this Saturday" using today's date.
- If the date cannot be established confidently, use null for start_date.
- For multi-day events, provide start_date and end_date.
- Do not return events whose dates are clearly in the past.
- Do not return council committee meetings, adult-only events, job adverts,
  generic service pages, or products for sale.
- A general attraction can be included when the page clearly presents it as
  an activity/day-out opportunity and gives a usable date.
- family_relevance is 1-5:
    5 = clearly designed for children/families
    3 = reasonably suitable for families/parents with children
    1 = not meaningfully relevant to families
- Niche interests can score highly when children could reasonably enjoy them:
  steam days, heritage transport, engineering museums, boat trips, farms,
  open days, etc.
- event_url must be the specific event URL when one is available.
- recurrence must be one of: one_off, recurring, seasonal, unknown.
- confidence is 0-1 and reflects how directly the page supports the extracted
  event details.
- Do not use information from your general knowledge. Use only the supplied
  content.

CONTENT:
{content}
"""


def make_gemini_caller():
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

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise FatalError("GEMINI_API_KEY is missing")

    client = genai.Client(api_key=api_key)

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
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=True
                        ),
                    ),
                )

                data = json.loads(response.text)

                if not isinstance(data, list):
                    raise ValueError("Gemini did not return a list")

                return data

            except Exception as exc:
                text = str(exc)

                if any(
                    word in text
                    for word in (
                        "NOT_FOUND",
                        "PERMISSION_DENIED",
                        "UNAUTHENTICATED",
                        "API key not valid",
                    )
                ):
                    raise FatalError(
                        f"Gemini rejected the request: {text[:300]}"
                    ) from exc

                last_error = exc
                time.sleep(5 * (attempt + 1))

        raise RuntimeError(
            f"Gemini failed after 3 tries: {last_error}"
        )

    return call


# ----------------------------------------------------------------------------
# Event validation
# ----------------------------------------------------------------------------
def validate_event_dates(start, end, today):
    min_date = today + dt.timedelta(days=MIN_EVENT_DAYS_FROM_TODAY)
    max_date = today + dt.timedelta(days=MAX_EVENT_DAYS_FROM_TODAY)

    # Default Dadspace behaviour is a forward-looking event window: the
    # advertised start date must be today or later. Optionally allow an
    # ongoing multi-day event that started earlier but has not ended.
    if start < min_date:
        if not (ALLOW_ONGOING_EVENTS and end >= min_date):
            return False, "event_finished"

    if start > max_date:
        return False, "event_too_far_in_future"

    return True, None


def clean_events(raw_events, source, page_url, method, today, stats):
    """Validate Gemini output and turn it into database rows."""
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    rows = {}

    for item in raw_events:
        stats["extracted"] += 1

        if not isinstance(item, dict):
            stats["invalid"] += 1
            continue

        title = clean_str(item.get("title"), 300)
        start = parse_date(item.get("start_date"))

        if not title:
            stats["invalid"] += 1
            continue

        if not start:
            stats["no_date"] += 1
            continue

        end = parse_date(item.get("end_date")) or start

        if end < start:
            end = start

        valid, reason = validate_event_dates(start, end, today)
        if not valid:
            stats[reason] += 1
            continue

        try:
            relevance = int(item.get("family_relevance") or 0)
        except (TypeError, ValueError):
            relevance = 0

        if relevance < MIN_RELEVANCE:
            stats["low_relevance"] += 1
            continue

        try:
            confidence = float(item.get("confidence") or 0)
        except (TypeError, ValueError):
            confidence = 0.0

        if confidence < MIN_CONFIDENCE:
            stats["low_confidence"] += 1
            continue

        location = clean_str(item.get("location"), 300)
        event_url = absolute_url(item.get("event_url"), page_url)

        key = make_dedupe_key(title, start, location)

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
            stats["duplicates"] += 1

            # Fill missing values from a duplicate occurrence.
            for field, value in new_row.items():
                if rows[key].get(field) is None and value is not None:
                    rows[key][field] = value
        else:
            rows[key] = new_row

    stats["kept"] += len(rows)
    return list(rows.values())


# ----------------------------------------------------------------------------
# One source
# ----------------------------------------------------------------------------
def process_source(source, extract, today):
    """
    Returns:
      status, rows, new_hash, message, stats
    """
    url = source["url"]

    allowed, reason = robots_allows(url)

    if not allowed:
        return (
            "skipped_robots",
            [],
            None,
            reason,
            {},
        )

    try:
        html = fetch_html(url)
    except Exception as exc:
        message = str(exc)

        if "http_404" in message:
            status = "failed_404"
        elif "http_403" in message:
            status = "failed_403"
        elif "timeout" in message.lower():
            status = "failed_timeout"
        elif "http_429" in message:
            status = "failed_429"
        else:
            status = "failed_fetch"

        return status, [], None, message, {}

    content, method = prepare_content(html, url)

    if len(content.strip()) < 200:
        return (
            "failed_no_content",
            [],
            None,
            "Page had almost no readable content; this source may belong "
            "in the browser workflow",
            {},
        )

    new_hash = hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

    stats = {
        "extracted": 0,
        "kept": 0,
        "invalid": 0,
        "no_date": 0,
        "event_finished": 0,
        "event_too_far_in_future": 0,
        "low_relevance": 0,
        "low_confidence": 0,
        "duplicates": 0,
    }

    raw = extract(
        build_prompt(
            source,
            url,
            content,
            today,
        )
    )

    rows = clean_events(
        raw,
        source,
        url,
        method,
        today,
        stats,
    )

    if not rows:
        status = "ok_zero"
    else:
        status = "ok"

    message = (
        f"{stats['extracted']} extracted, "
        f"{len(rows)} kept"
    )

    return status, rows, new_hash, message, stats


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    missing = [
        name
        for name in (
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "GEMINI_API_KEY",
        )
        if not os.environ.get(name)
    ]

    if missing:
        print(
            "Setup problem: missing secrets: "
            + ", ".join(missing)
        )
        sys.exit(1)

    supabase_url = (
        os.environ["SUPABASE_URL"]
        .strip()
        .strip("\"'")
        .rstrip("/")
    )
    supabase_key = (
        os.environ["SUPABASE_KEY"]
        .strip()
        .strip("\"'")
    )

    if not re.fullmatch(
        r"https://[A-Za-z0-9-]+\.supabase\.co",
        supabase_url,
    ):
        print("Setup problem: SUPABASE_URL does not look valid.")
        sys.exit(1)

    from supabase import create_client

    db = create_client(
        supabase_url,
        supabase_key,
    )

    extract = make_gemini_caller()
    today = today_uk()

    query = (
        db.table("sources")
        .select("*")
        .eq("active", True)
    )

    if CATEGORY_FILTER:
        query = query.in_(
            "category",
            CATEGORY_FILTER,
        )

    sources = query.execute().data or []

    # Never-checked sources first, then oldest checked.
    sources.sort(
        key=lambda s: s.get("last_checked_at") or ""
    )

    if LIMIT > 0:
        sources = sources[:LIMIT]

    which = ", ".join(CATEGORY_FILTER) or "all categories"

    print(
        f"Today (UK): {today}. "
        f"Categories: {which}. "
        f"Fetch engine: {FETCH_ENGINE}. "
        f"Sources: {len(sources)}. "
        f"Dry run: {DRY_RUN}. "
        f"Model: {MODEL}"
    )

    print(
        f"Event window: "
        f"{MIN_EVENT_DAYS_FROM_TODAY} to "
        f"{MAX_EVENT_DAYS_FROM_TODAY} days from today"
    )

    totals = {}
    total_events = 0
    zero_event_sources = []
    run_stats = {
        "extracted": 0,
        "kept": 0,
        "invalid": 0,
        "no_date": 0,
        "event_finished": 0,
        "event_too_far_in_future": 0,
        "low_relevance": 0,
        "low_confidence": 0,
        "duplicates": 0,
    }

    for number, source in enumerate(
        sources,
        start=1,
    ):
        label = f"[{number}/{len(sources)}] {source['name']}"
        now_iso = dt.datetime.now(
            dt.timezone.utc
        ).isoformat()

        update = {
            "last_checked_at": now_iso,
        }

        try:
            (
                status,
                rows,
                new_hash,
                message,
                stats,
            ) = process_source(
                source,
                extract,
                today,
            )

        except FatalError as exc:
            print(
                f"{label}: STOPPING WHOLE RUN - {exc}"
            )
            sys.exit(1)

        except Exception as exc:
            status = "failed_unexpected"
            rows = []
            new_hash = None
            message = (
                f"{type(exc).__name__}: {exc}"
            )
            stats = {}

        totals[status] = totals.get(status, 0) + 1

        for key in run_stats:
            run_stats[key] += stats.get(key, 0)

        print(
            f"{label}: {status.upper()} - {message}"
        )

        if status in ("ok", "ok_zero"):
            update.update({
                "last_hash": new_hash,
                "last_success_at": now_iso,
                "fail_count": 0,
                "last_error": None,
                "last_event_count": len(rows),
            })

            total_events += len(rows)

            if status == "ok_zero":
                zero_event_sources.append(
                    source["name"]
                )

            if rows and not DRY_RUN:
                db.table(EVENTS_TABLE).upsert(
                    rows,
                    on_conflict="dedupe_key",
                ).execute()

            if DRY_RUN:
                for row in rows[:5]:
                    print(
                        f"      would save: "
                        f"{row['start_date']} | "
                        f"{row['title']} | "
                        f"{row['location']}"
                    )

        else:
            update.update({
                "fail_count": (
                    source.get("fail_count") or 0
                ) + 1,
                "last_error": message[:500],
            })

        if not DRY_RUN:
            db.table("sources").update(
                update
            ).eq(
                "id",
                source["id"],
            ).execute()

        time.sleep(PAUSE_SECONDS)

    print("\n=== Summary ===")
    print(
        f"Valid events: {total_events}"
        + (
            " (dry run - nothing was saved)"
            if DRY_RUN
            else ""
        )
    )

    print(
        "Sources: "
        + ", ".join(
            f"{key}={value}"
            for key, value in sorted(totals.items())
        )
    )

    print(
        "Event policy: "
        f"start >= {today.isoformat()}, "
        f"max start = {(today + dt.timedelta(days=MAX_EVENT_DAYS_FROM_TODAY)).isoformat()}, "
        f"ongoing_started_before_today={ALLOW_ONGOING_EVENTS}"
    )

    print(
        "Events: "
        f"extracted={run_stats['extracted']}, "
        f"kept={run_stats['kept']}, "
        f"past={run_stats['event_finished']}, "
        f"too_far={run_stats['event_too_far_in_future']}, "
        f"no_date={run_stats['no_date']}, "
        f"low_relevance={run_stats['low_relevance']}, "
        f"low_confidence={run_stats['low_confidence']}, "
        f"duplicates={run_stats['duplicates']}"
    )

    if zero_event_sources:
        print(
            "Worked but found 0 valid events "
            "(worth checking): "
            + "; ".join(zero_event_sources)
        )


if __name__ == "__main__":
    main()

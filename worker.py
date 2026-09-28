"""
Dadspace family events collector - v5.

One file, used by both scheduled workflows (collect-civic.yml sets
FETCH_ENGINE=requests; collect-activities.yml sets FETCH_ENGINE=browser).

v5 adds, on top of the v4 improvements (retry session, clearer per-source
error classes, JSON-LD combined with visible text, a configurable
forward-looking event date window, per-event rejection counters):
  - a hard MAX_RUN_MINUTES budget so a run can never run away
  - per-source elapsed-time reporting
  - a timeout around the Gemini call specifically, so one bad page can't
    hang the whole run
  - a guaranteed summary via try/finally, built only from variables that
    are set before the loop starts, so a bug late in the run can't erase
    the report of everything that already succeeded
  - a top-level catch-all so the script always exits with a clear message
  - a --self-test mode that exercises the important logic with no network,
    Gemini, or Supabase calls, for use as a pre-flight check
  - defensive handling around each Supabase write, so a transient database
    hiccup doesn't take down the whole run

Nothing here changes what gets fetched or how: the browser (Playwright) path
is untouched and is not given any of this new machinery beyond what the
shared loop already provides (the run budget and per-source timing apply to
it too, since it's the same loop) - no new browser-specific code was added.

Note on the events actually being safe: because each source's events and
status are written to Supabase right after that source is processed (not
batched up at the end), a crash in the final summary print was never able
to lose already-collected events - only the printed report of the run.
This version just makes sure that report can no longer fail either.
"""

import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from urllib import robotparser
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ----------------------------------------------------------------------------
# Settings (all can be changed from GitHub without editing this file)
# ----------------------------------------------------------------------------
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-3.6-flash"
FETCH_ENGINE = (os.environ.get("FETCH_ENGINE", "requests") or "requests").strip().lower()
CATEGORY_FILTER = [c.strip() for c in os.environ.get("CATEGORIES", "").split(",") if c.strip()]
EVENTS_TABLE = os.environ.get("EVENTS_TABLE", "collected_events")
LIMIT = int(os.environ.get("LIMIT", "0") or 0)
DRY_RUN = os.environ.get("DRY_RUN", "false").strip().lower() == "true"

MIN_RELEVANCE = int(os.environ.get("MIN_RELEVANCE", "3"))
MIN_CONFIDENCE = float(os.environ.get("MIN_CONFIDENCE", "0.0"))

MAX_CHARS = int(os.environ.get("MAX_CHARS", "40000"))
MAX_JSONLD_CHARS = int(os.environ.get("MAX_JSONLD_CHARS", "12000"))
OXFORDSHIRE_MAX_PAGES = int(os.environ.get("OXFORDSHIRE_MAX_PAGES", "3"))

PAUSE_SECONDS = float(os.environ.get("PAUSE_SECONDS", "2"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "2"))
BROWSER_GOTO_TIMEOUT_MS = int(os.environ.get("BROWSER_GOTO_TIMEOUT_MS", "30000"))
BROWSER_SETTLE_MS = int(os.environ.get("BROWSER_SETTLE_MS", "2500"))

# v4: hard budget on the whole run, and a separate one just for Gemini calls.
MAX_RUN_MINUTES = float(os.environ.get("MAX_RUN_MINUTES", "45"))
GEMINI_TIMEOUT_SECONDS = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "60"))

# Events whose end date passed more than this many days ago are deleted at the
# end of each run. Set to -1 to switch clean-up off. The app itself should read
# the upcoming_events view (see expired_events.sql), which hides finished events
# immediately, whatever this is set to.
EXPIRED_RETENTION_DAYS = int(os.environ.get("EXPIRED_RETENTION_DAYS", "30"))

# Only events whose advertised start date falls in this forward-looking
# window (relative to today) are kept. ALLOW_ONGOING_EVENTS additionally
# keeps a multi-day event that started earlier but has not ended yet.
MIN_EVENT_DAYS_FROM_TODAY = int(os.environ.get("MIN_EVENT_DAYS_FROM_TODAY", "0"))
MAX_EVENT_DAYS_FROM_TODAY = int(os.environ.get("MAX_EVENT_DAYS_FROM_TODAY", "365"))
ALLOW_ONGOING_EVENTS = os.environ.get("ALLOW_ONGOING_EVENTS", "false").strip().lower() == "true"

USER_AGENT = os.environ.get("USER_AGENT", "Mozilla/5.0 (compatible; DadspaceEventsBot/1.0)")
TIMEZONE = ZoneInfo("Europe/London")

EVENT_FIELDS = [
    "title", "description", "start_date", "end_date", "time_text", "location",
    "event_url", "cost_text", "age_range", "recurrence", "family_relevance", "confidence",
]


class FatalError(Exception):
    """A problem that affects every source, not just one (bad key, bad model
    name, bad Supabase URL). Stops the whole run rather than being retried
    site by site."""


# ----------------------------------------------------------------------------
# HTTP session (requests path only - browser path is unaffected)
# ----------------------------------------------------------------------------
def make_http_session():
    retry = Retry(
        total=MAX_RETRIES,
        connect=0,          # a site that won't even answer is not retried (was the cause of ~140s waits)
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


def normalise_text(value):
    return re.sub(r"\s+", " ", (value or "").lower()).strip()


def make_dedupe_key(title, start_date, location):
    """Same title + date + place = same event, regardless of which website
    found it - so overlapping sources merge instead of duplicating."""
    raw = "|".join([normalise_text(title), str(start_date), normalise_text(location)])
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


def classify_fetch_error(message):
    text = (message or "").lower()
    if "http_404" in text:
        return "failed_404"
    if "http_403" in text:
        return "failed_403"
    if "http_429" in text:
        return "failed_429"
    if "timed out" in text or "timeout" in text:
        return "failed_timeout"
    return "failed_fetch"


def expiry_cutoff(today, retention_days):
    """Events that ended before this date are old enough to delete."""
    return today - dt.timedelta(days=retention_days)


def call_with_timeout(fn, timeout_seconds):
    """Run fn() with a hard wall-clock timeout. Used only around the Gemini
    call, so one slow/stuck page can't hold up the whole run. Note: this
    can't truly cancel a stuck network call inside the worker thread - it
    just stops WAITING for it and lets the run move on; the abandoned thread
    is cleaned up when the process exits."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            return future.result(timeout=timeout_seconds)
        except FutureTimeoutError:
            raise RuntimeError(f"timed out after {timeout_seconds}s")


# ----------------------------------------------------------------------------
# Robots
# ----------------------------------------------------------------------------
def robots_allows(url):
    """Respect the website's robots.txt. A robots.txt that itself errors or
    is missing tells us nothing, so that counts as "allowed", not blocked -
    only an actual disallow rule blocks the fetch."""
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        resp = HTTP.get(robots_url, timeout=15)
    except requests.ConnectTimeout as exc:
        # The server never answered at all, so fetching the page itself would
        # just wait again. Fail now instead of waiting a second time.
        raise RuntimeError(f"timeout after 15s connecting to {parts.netloc}: {exc}") from exc
    except requests.RequestException:
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
    """Plain download - fast, works for ordinary web pages."""
    try:
        resp = HTTP.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    except requests.Timeout as exc:
        raise RuntimeError(f"timeout after {REQUEST_TIMEOUT}s: {exc}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"request error: {exc}") from exc

    status = classify_http_status(resp.status_code)
    if status != "success":
        raise RuntimeError(f"{status}: {resp.url or url}")

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if content_type and not any(
        t in content_type for t in ("text/html", "application/xhtml+xml", "application/json")
    ):
        raise RuntimeError(f"unexpected content type {content_type}")

    if not resp.text.strip():
        raise RuntimeError("empty response body")

    return resp.text


def _alternate_https_host(url):
    """Return the same HTTPS URL with www. toggled, for certificate-hostname
    failures only. This is deliberately narrow: TLS verification stays enabled."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return None
    host = parsed.netloc
    alt_host = host[4:] if host.lower().startswith("www.") else "www." + host
    return parsed._replace(netloc=alt_host).geturl()


def fetch_html_browser(url):
    """Load a JavaScript page without waiting for global network idleness.

    Modern directory sites often keep analytics/polling requests open forever,
    so ``networkidle`` can time out even though the useful DOM is already ready.
    Wait for DOMContentLoaded, allow a short bounded JS settle, then snapshot the
    DOM. On the specific TLS common-name error, try the same URL once with the
    www host toggled; certificate verification is never disabled.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            candidates = [url]
            alt = _alternate_https_host(url)
            if alt and alt != url:
                candidates.append(alt)

            last_error = None
            for index, candidate in enumerate(candidates):
                try:
                    page.goto(candidate, timeout=BROWSER_GOTO_TIMEOUT_MS, wait_until="domcontentloaded")
                    page.wait_for_timeout(BROWSER_SETTLE_MS)
                    return page.content()
                except Exception as exc:
                    last_error = exc
                    # Only try the alternate hostname for the certificate-name
                    # mismatch seen on legacy/misconfigured domains.
                    if index == 0 and "ERR_CERT_COMMON_NAME_INVALID" in str(exc):
                        continue
                    raise
            raise last_error
        finally:
            browser.close()


def fetch_html(url):
    if FETCH_ENGINE == "browser":
        return fetch_html_browser(url)
    if FETCH_ENGINE == "requests":
        return fetch_html_requests(url)
    raise FatalError(f"Unknown FETCH_ENGINE={FETCH_ENGINE!r}; expected 'requests' or 'browser'")


# ----------------------------------------------------------------------------
# Content extraction
# ----------------------------------------------------------------------------
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
    """Many sites embed machine-readable events (schema.org). If present,
    pull them out - but keep the visible text too (see prepare_content)."""
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
            if any(isinstance(t, str) and t.lower().endswith("event") for t in types):
                found.append(item)
    return found


def page_to_text(soup, base_url):
    """Strip menus/scripts and keep readable text, with link addresses next
    to link text."""
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "form", "nav", "footer"]):
        tag.decompose()
    for link in soup.find_all("a", href=True):
        label = link.get_text(" ", strip=True)
        href = absolute_url(link["href"], base_url)
        if label and href:
            link.replace_with(f"{label} [{href}]")
    text = soup.get_text("\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)



def extract_eventish_html(soup, base_url):
    """Preserve event-like table/list rows in a compact, highly visible block.

    Some council pages are perfectly server-rendered but their event listings
    are surrounded by filters/navigation. Giving Gemini a compact rendering of
    rows/cards makes those pages much more reliable without requiring a browser.
    """
    rows = []

    # Tables are especially common on council event pages.
    for tr in soup.find_all("tr"):
        cells = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)).strip()
                 for c in tr.find_all(["th", "td"])]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            links = []
            for a in tr.find_all("a", href=True):
                href = absolute_url(a.get("href"), base_url)
                label = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                if href and label:
                    links.append(f"{label} [{href}]")
            line = " | ".join(cells)
            if links:
                line += " | LINKS: " + " ; ".join(dict.fromkeys(links))
            rows.append(line)

    # If there is no useful table, preserve common event-card/list containers.
    if not rows:
        selectors = [
            "article", ".event", ".event-card", ".event-item", ".views-row",
            ".listing-item", ".card", "li",
        ]
        seen = set()
        for selector in selectors:
            for node in soup.select(selector):
                line = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
                if len(line) < 20 or len(line) > 1200:
                    continue
                links = []
                for a in node.find_all("a", href=True):
                    href = absolute_url(a.get("href"), base_url)
                    label = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                    if href and label:
                        links.append(f"{label} [{href}]")
                if links:
                    line += " | LINKS: " + " ; ".join(dict.fromkeys(links))
                if line not in seen:
                    seen.add(line)
                    rows.append(line)
                if len(rows) >= 150:
                    break
            if rows:
                break

    return "\n".join(rows[:150])


def source_fetch_urls(source):
    """Return one or more useful listing URLs for a source.

    Almost every source is just its one stored URL. Oxfordshire's council
    events page is the one exception that needs more than one page per run,
    handled with an explicit page-number pattern below.
    """
    url = source["url"]
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/")

    if host.endswith("oxfordshire.gov.uk") and path == "/events":
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        count = max(1, min(OXFORDSHIRE_MAX_PAGES, 10))
        return [
            f"{base}?event_category=All&venue=&page={page}"
            for page in range(count)
        ]

    return [url]


def fetch_source_html(source):
    """Fetch all request documents needed for one source and combine them.

    Browser directory sources may load a small bounded set of public location
    listing pages; requests sources may use narrow source-specific pagination.
    """
    urls = source_fetch_urls(source)
    documents = []
    for i, url in enumerate(urls):
        if i:
            allowed, reason = robots_allows(url)
            if not allowed:
                break
        html = fetch_html(url)
        documents.append((url, html))
    return documents

def prepare_content(html, url):
    """Return (content_for_gemini, method_label).

    `html` may be one HTML string or a list of (page_url, html) documents.
    Structured JSON-LD, compact event rows/cards, and visible page text are
    combined. The compact event block is placed first so a long council page
    cannot push the actual listings beyond MAX_CHARS.
    """
    documents = html if isinstance(html, list) else [(url, html)]

    event_blocks = []
    jsonld_all = []
    visible_blocks = []

    for page_url, page_html in documents:
        soup = BeautifulSoup(page_html, "html.parser")
        jsonld_all.extend(extract_jsonld_events(soup))

        compact = extract_eventish_html(soup, page_url)
        if compact:
            event_blocks.append(f"PAGE: {page_url}\n{compact}")

        visible = page_to_text(soup, page_url)
        if visible:
            visible_blocks.append(f"PAGE: {page_url}\n{visible}")

    parts = []
    if event_blocks:
        parts.append("COMPACT EVENT LISTINGS FROM HTML:\n" + "\n\n".join(event_blocks))
    if jsonld_all:
        jsonld_text = json.dumps(jsonld_all, ensure_ascii=False)
        parts.append("STRUCTURED EVENT DATA (schema.org JSON-LD):\n" + jsonld_text[:MAX_JSONLD_CHARS])
    if visible_blocks:
        parts.append("VISIBLE PAGE TEXT:\n" + "\n\n".join(visible_blocks))

    # Allocate space in order of usefulness. Event rows/cards come first.
    remaining = MAX_CHARS
    kept = []
    for part in parts:
        if remaining <= 0:
            break
        piece = part[:remaining]
        kept.append(piece)
        remaining -= len(piece)

    content = "\n\n".join(kept)[:MAX_CHARS]
    if jsonld_all and event_blocks:
        method = "html-listings+jsonld+llm"
    elif jsonld_all:
        method = "jsonld+llm"
    elif event_blocks:
        method = "html-listings+llm"
    else:
        method = "llm"
    return content, method


# ----------------------------------------------------------------------------
# Gemini
# ----------------------------------------------------------------------------
def build_prompt(source, url, content, today):
    return f"""You extract public events from a web page for Dadspace, a UK database of things for parents, dads and families to do with children.

Today's date is {today.isoformat()} (UK). The page is from "{source['name']}" ({url}).

Return a JSON list of events found in the supplied content.

IMPORTANT RULES:
- Only include real, specific events, open days, activities or attractions with a date. Never invent details.
- Only use dates supported by the supplied content.
- Dates must be ISO format YYYY-MM-DD. Resolve relative dates ("this Saturday") using today's date.
- If the date cannot be established confidently, use null for start_date.
- For multi-day events, provide start_date and end_date.
- A page may contain compact table/list rows from several pagination pages. Treat each row as a candidate event and deduplicate repeated occurrences/details.
- Some recurring council listings incorrectly expose a far-future series boundary as if it were an individual event end date (for example a 30-minute Rhymetime row starting in 2026 and apparently ending in 2030). For an obviously short recurring session, use the occurrence date as both start_date and end_date, keep the displayed session times in time_text, and set recurrence to recurring. Do not turn a short session into a multi-year event.
- Do not return events whose dates are clearly in the past.
- Skip council committee meetings, adult-only events, job adverts, generic service pages, and things only for sale.
- A general attraction can be included when the page clearly presents it as an activity/day-out opportunity with a usable date.
- The audience is fathers and other parents looking for genuine activities they can do WITH their children. Be conservative: this is a parent-activity database, not a general local events calendar.
- Only include an event when the supplied content gives a concrete reason it belongs in a parent/family activity database.
- family_relevance is 1-5:
    5 = explicitly designed for children/families, or an unmistakably child/family-oriented activity (for example junior sport, Forest School, children's workshop, family trail, teddy bears' picnic, farm activity, family boat trip, steam/heritage open day with a genuine activity, hands-on museum activity).
    4 = clearly suitable for a parent and child together, even if not exclusively child-focused; the supplied content must contain concrete evidence of that suitability.
    3 = potentially suitable but the page gives only limited evidence; use this score only when there is still a concrete family/child/activity signal in the supplied content.
    2 = mainly adult/general-interest and not clearly a parent-child activity.
    1 = adult-only, unsuitable, administrative, commercial, or not a genuine activity/event.
- Do NOT give 3 or higher merely because children are not excluded, an attraction exists, an event is local/free, or you can imagine a family enjoying it.
- Treat these as NOT parent activities unless the content explicitly shows a child/family component: adult talks/lectures, adult education, instrument or craft classes aimed at adults, book groups, business/networking meetings, political meetings, committee meetings, religious services, remembrance/memorial events, fundraising coffee mornings, professional events, job adverts, generic attraction listings, and things for sale.
- A general attraction may be included only when the supplied page presents a specific dated activity/day-out opportunity (for example an open day, steam day, family trail, guided activity, workshop, special tour or similar). Do not turn ordinary opening information, membership information, ticket sales or equipment hire into events.
- Return two additional fields:
    audience = one of: children, families, general, adults, unknown.
    family_evidence = a short phrase copied or closely paraphrased from the supplied content explaining why a parent would do this with a child. If there is no concrete evidence, use null.
- For family_relevance 3 or 4, family_evidence is required. For 5, it should normally be present too. Never invent evidence.
- event_url should be the specific event link if one appears in the content (links appear as [url] after the link text).
- recurrence is one of: one_off, recurring, seasonal, unknown.
- confidence is 0-1: how sure you are the event details and family evidence are correct and come from the supplied content.
- Do not use information from your general knowledge - use only the supplied content.

CONTENT:
{content}
"""


def make_gemini_caller():
    """Set up the Gemini client. Imported here so the rest of the file can be
    tested (including --self-test) without these libraries being required."""
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
        audience: Optional[str] = None
        family_evidence: Optional[str] = None

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise FatalError("GEMINI_API_KEY is missing")

    client = genai.Client(api_key=api_key)

    def call(prompt):
        last_error = None
        for attempt in range(3):
            try:
                def do_call():
                    return client.models.generate_content(
                        model=MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=list[EventSchema],
                            temperature=0,
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                        ),
                    )

                response = call_with_timeout(do_call, GEMINI_TIMEOUT_SECONDS)
                data = json.loads(response.text)
                if not isinstance(data, list):
                    raise ValueError("Gemini did not return a list")
                return data
            except Exception as exc:
                text = str(exc)
                if any(word in text for word in ("NOT_FOUND", "PERMISSION_DENIED", "UNAUTHENTICATED", "API key not valid")):
                    raise FatalError(
                        f"Gemini rejected the request ({text[:300]}). "
                        "The model name may be retired (change the GEMINI_MODEL variable in GitHub) "
                        "or the GEMINI_API_KEY secret may be wrong."
                    ) from exc
                last_error = exc
                time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"Gemini failed after 3 tries: {last_error}")

    return call


# ----------------------------------------------------------------------------
# Event validation
# ----------------------------------------------------------------------------
def validate_event_dates(start, end, today):
    min_date = today + dt.timedelta(days=MIN_EVENT_DAYS_FROM_TODAY)
    max_date = today + dt.timedelta(days=MAX_EVENT_DAYS_FROM_TODAY)
    if start < min_date:
        if not (ALLOW_ONGOING_EVENTS and end >= min_date):
            return False, "event_finished"
    if start > max_date:
        return False, "event_too_far_in_future"
    return True, None


def clean_events(raw_events, source, page_url, method, today, stats=None):
    """Validate what Gemini returned and turn it into database rows.
    stats, when given, is updated in place with counts for each rejection
    reason (used for --self-test and the run summary)."""
    if stats is None:
        stats = {}
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    rows = {}

    for item in raw_events:
        stats["extracted"] = stats.get("extracted", 0) + 1
        if not isinstance(item, dict):
            stats["invalid"] = stats.get("invalid", 0) + 1
            continue

        title = clean_str(item.get("title"), 300)
        start = parse_date(item.get("start_date"))
        if not title:
            stats["invalid"] = stats.get("invalid", 0) + 1
            continue
        if not start:
            stats["no_date"] = stats.get("no_date", 0) + 1
            continue

        end = parse_date(item.get("end_date")) or start
        if end < start:
            end = start

        valid, reason = validate_event_dates(start, end, today)
        if not valid:
            stats[reason] = stats.get(reason, 0) + 1
            continue

        try:
            relevance = int(item.get("family_relevance") or 0)
        except (TypeError, ValueError):
            relevance = 0
        if relevance < MIN_RELEVANCE:
            stats["low_relevance"] = stats.get("low_relevance", 0) + 1
            samples = stats.setdefault("low_relevance_samples", [])
            if len(samples) < 3:
                samples.append(f"{title} (scored {relevance}/5)")
            continue

        # v5: relevance is not just a model score. Require a concrete
        # family/child/activity signal for borderline/general events.
        audience = normalise_text(item.get("audience"))
        family_evidence = clean_str(item.get("family_evidence"), 500)
        allowed_audiences = {"children", "families", "general", "adults", "unknown"}
        if audience not in allowed_audiences:
            audience = "unknown"

        if audience == "adults":
            stats["not_parent_activity"] = stats.get("not_parent_activity", 0) + 1
            continue

        # An audience of "children" or "families" is itself the evidence, at
        # any relevance score. Anything else ("general" or "unknown") needs a
        # concrete reason in the content - otherwise a high score with no real
        # basis (e.g. a generic attraction page) would slip straight through,
        # which defeats the point of asking for evidence at all.
        if audience not in ("children", "families") and not family_evidence:
            stats["missing_family_evidence"] = stats.get("missing_family_evidence", 0) + 1
            samples = stats.setdefault("missing_family_evidence_samples", [])
            if len(samples) < 3:
                samples.append(f"{title} (scored {relevance}/5, audience: {audience})")
            continue

        try:
            confidence = float(item.get("confidence") or 0)
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence < MIN_CONFIDENCE:
            stats["low_confidence"] = stats.get("low_confidence", 0) + 1
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
            stats["duplicates"] = stats.get("duplicates", 0) + 1
            for field, value in new_row.items():
                if rows[key].get(field) is None and value is not None:
                    rows[key][field] = value
        else:
            rows[key] = new_row

    stats["kept"] = stats.get("kept", 0) + len(rows)
    return list(rows.values())


# ----------------------------------------------------------------------------
# One source
# ----------------------------------------------------------------------------
def content_diagnostics(documents, content):
    """Small, non-sensitive diagnostics for any OK_ZERO source.

    These distinguish a genuine zero-event listing from a page that loaded
    (or was rendered) but didn't have the content we expected, without
    dumping raw page content into CI logs.
    """
    docs = documents if isinstance(documents, list) else [("", documents)]
    html_chars = sum(len(html or "") for _, html in docs)
    jsonld_events = 0
    eventish_rows = 0
    titles = []
    for _, html in docs:
        soup = BeautifulSoup(html or "", "html.parser")
        jsonld_events += len(extract_jsonld_events(soup))
        compact = extract_eventish_html(soup, source_url := (_ or ""))
        if compact:
            eventish_rows += len(compact.splitlines())
        if soup.title and soup.title.get_text(strip=True):
            titles.append(re.sub(r"\s+", " ", soup.title.get_text(" ", strip=True))[:100])
    title = " | ".join(dict.fromkeys(titles))[:160] or "(none)"
    return f"html_chars={html_chars}, content_chars={len(content)}, jsonld_events={jsonld_events}, eventish_rows={eventish_rows}, title={title}"


def process_source(source, extract, today):
    """Returns (status, event_rows, new_hash, message, stats)."""
    url = source["url"]
    stats = {}

    try:
        allowed, reason = robots_allows(url)
    except Exception as exc:
        return classify_fetch_error(str(exc)), [], None, str(exc), stats
    if not allowed:
        return "skipped_robots", [], None, reason, stats

    try:
        documents = fetch_source_html(source)
    except FatalError:
        raise
    except Exception as exc:
        return classify_fetch_error(str(exc)), [], None, str(exc), stats

    content, method = prepare_content(documents, url)
    if len(content.strip()) < 200:
        return (
            "failed_no_content", [], None,
            "Page had almost no readable content (it may need the browser workflow)",
            stats,
        )

    new_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if new_hash == source.get("last_hash") and source.get("last_success_at"):
        return "unchanged", [], new_hash, "Page unchanged since last run", stats

    raw = extract(build_prompt(source, url, content, today))
    rows = clean_events(raw, source, url, method, today, stats)
    status = "ok" if rows else "ok_zero"
    message = f"{stats.get('extracted', 0)} extracted, {len(rows)} kept"
    if status == "ok_zero":
        message += "; diagnostics: " + content_diagnostics(documents, content)
    rejected = {k: v for k, v in stats.items() if k not in ("extracted", "kept", "duplicates") and v}
    if rejected:
        message += "; rejected: " + ", ".join(f"{k}={v}" for k, v in sorted(rejected.items()))
    if stats.get("duplicates"):
        message += f"; merged duplicates={stats['duplicates']}"
    return status, rows, new_hash, message, stats


# ----------------------------------------------------------------------------
# Saving events
# ----------------------------------------------------------------------------
def save_events(db, rows):
    """Save a source's events. Returns None on success, or a short error message.
    The caller must NOT record the page as 'done' if this fails, otherwise the
    unchanged-page check would skip that page next time and its events would
    never be saved."""
    try:
        db.table(EVENTS_TABLE).upsert(rows, on_conflict="dedupe_key").execute()
        return None
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


def check_events_table(db):
    """Returns None if the events table can be read, otherwise the error text."""
    try:
        db.table(EVENTS_TABLE).select("id").limit(1).execute()
        return None
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"


# ----------------------------------------------------------------------------
# Expired events
# ----------------------------------------------------------------------------
def remove_expired_events(db, today):
    """Delete saved events that finished more than EXPIRED_RETENTION_DAYS ago.
    Needed because a page that has not changed is not re-read, so its old
    events would otherwise sit in the table for ever. Returns how many were
    removed (in a dry run: how many would be), or None if clean-up is off.
    A past event can't come back: the date check in clean_events rejects it."""
    if EXPIRED_RETENTION_DAYS < 0:
        return None
    cutoff = expiry_cutoff(today, EXPIRED_RETENTION_DAYS).isoformat()
    table = db.table(EVENTS_TABLE)
    if DRY_RUN:
        resp = table.select("id", count="exact").lt("end_date", cutoff).execute()
        return resp.count or 0
    resp = table.delete().lt("end_date", cutoff).execute()
    return len(resp.data or [])


# ----------------------------------------------------------------------------
# Self-test - no network, Gemini, or Supabase involved
# ----------------------------------------------------------------------------
def self_test():
    failures = []

    def check(label, condition):
        print(f"  [{'ok' if condition else 'FAIL'}] {label}")
        if not condition:
            failures.append(label)

    print("Self-test (no network/Gemini/Supabase calls made)")

    check("parse_date handles a plain date", parse_date("2026-10-04") == dt.date(2026, 10, 4))
    check("parse_date handles a date with a time", parse_date("2026-10-04T10:00:00") == dt.date(2026, 10, 4))
    check("parse_date rejects nonsense", parse_date("not a date") is None)
    check("parse_date rejects None", parse_date(None) is None)

    check("classify_http_status maps 404", classify_http_status(404) == "http_404")
    check("classify_http_status maps 403", classify_http_status(403) == "http_403")
    check("classify_http_status maps 200", classify_http_status(200) == "success")
    check("classify_http_status maps 503", classify_http_status(503) == "http_5xx")

    same_key = make_dedupe_key("Steam Day", dt.date(2026, 10, 4), "Kempton")
    other_key = make_dedupe_key("Steam Day", dt.date(2026, 10, 4), "Kempton")
    diff_key = make_dedupe_key("Different Event", dt.date(2026, 10, 4), "Kempton")
    check("make_dedupe_key is stable for the same event", same_key == other_key)
    check("make_dedupe_key differs for a different event", same_key != diff_key)

    check("absolute_url resolves a relative link", absolute_url("/e/1", "https://x.org/events") == "https://x.org/e/1")
    check("absolute_url rejects garbage", absolute_url("javascript:void(0)", "https://x.org") is None)
    check("certificate fallback removes www", _alternate_https_host("https://www.example.org/events") == "https://example.org/events")
    check("certificate fallback adds www", _alternate_https_host("https://example.org/events") == "https://www.example.org/events")

    today = dt.date(2026, 9, 27)
    src = {"id": "self-test-source"}
    raw = [
        {"title": "Future family day", "start_date": "2026-10-04", "location": "Town Hall", "family_relevance": 5, "confidence": 0.9, "audience": "families", "family_evidence": "family activity"},
        {"title": "Past thing", "start_date": "2023-02-20", "family_relevance": 5, "confidence": 0.9, "audience": "families", "family_evidence": "family activity"},
        {"title": "No date", "start_date": None, "family_relevance": 5, "confidence": 0.9, "audience": "families", "family_evidence": "family activity"},
        {"title": "Adult only", "start_date": "2026-10-10", "family_relevance": 1, "confidence": 0.9, "audience": "adults"},
        {"title": "Borderline without evidence", "start_date": "2026-10-11", "family_relevance": 4, "confidence": 0.9, "audience": "general"},
        {"title": "Adult audience despite high score", "start_date": "2026-10-12", "family_relevance": 5, "confidence": 0.9, "audience": "adults", "family_evidence": "adult class"},
        {"title": "Future family day", "start_date": "2026-10-04", "location": "Town Hall", "family_relevance": 4, "cost_text": "Free", "audience": "families", "family_evidence": "family activity"},
        {"title": "Too far ahead", "start_date": "2028-01-01", "family_relevance": 5, "confidence": 0.9, "audience": "families", "family_evidence": "family activity"},
    ]
    stats = {}
    rows = clean_events(raw, src, "https://x.org/events", "llm", today, stats)
    check("clean_events keeps only the valid future event", [r["title"] for r in rows] == ["Future family day"])
    check("clean_events merges the duplicate rather than adding a second row", rows[0]["cost_text"] == "Free")
    check("clean_events filtered the past event", stats.get("event_finished") == 1)
    check("clean_events filtered the dateless event", stats.get("no_date") == 1)
    check("clean_events filtered the low-relevance event", stats.get("low_relevance") == 1)
    check("clean_events filtered the missing-family-evidence event", stats.get("missing_family_evidence") == 1)
    check("clean_events filtered the adult-audience event", stats.get("not_parent_activity") == 1)
    sample_html = """<table><tr><th>Title</th><th>Location</th><th>Date</th></tr>
    <tr><td><a href="/events/lego">Lego Club</a></td><td>Library</td><td>1 October 2026</td></tr></table>"""
    compact = extract_eventish_html(BeautifulSoup(sample_html, "html.parser"), "https://example.org/events")
    check("HTML event table rows are preserved", "Lego Club" in compact and "1 October 2026" in compact)

    ox_urls = source_fetch_urls({"url": "https://www.oxfordshire.gov.uk/events"})
    check("Oxfordshire uses explicit all-events pagination",
          len(ox_urls) >= 1 and "event_category=All" in ox_urls[0])
    other_urls = source_fetch_urls({"url": "https://example.org/whats-on"})
    check("an ordinary source is fetched at its one stored URL", other_urls == ["https://example.org/whats-on"])

    gap_case = {"title": "General attraction", "start_date": "2026-10-05", "location": "Somewhere",
                "family_relevance": 5, "confidence": 0.9, "audience": "general"}
    gap_stats = {}
    gap_rows = clean_events([gap_case], src, "https://x.org/events", "llm", today, gap_stats)
    check("a high-scoring 'general' event with no evidence is rejected, not kept",
          gap_rows == [] and gap_stats.get("missing_family_evidence") == 1)
    families_case = {"title": "Family day", "start_date": "2026-10-05", "location": "Somewhere",
                      "family_relevance": 5, "confidence": 0.9, "audience": "families"}
    families_rows = clean_events([families_case], src, "https://x.org/events", "llm", today, {})
    check("an event the model already labelled 'families' needs no extra evidence", len(families_rows) == 1)
    check("clean_events filtered the too-far-ahead event", stats.get("event_too_far_in_future") == 1)
    check("clean_events counted the duplicate", stats.get("duplicates") == 1)
    accounted = stats["kept"] + stats["duplicates"] + sum(
        stats.get(k, 0) for k in ("invalid", "no_date", "event_finished", "event_too_far_in_future",
                                  "low_relevance", "not_parent_activity", "missing_family_evidence", "low_confidence"))
    check("every extracted event is accounted for (kept, merged or rejected)", accounted == stats["extracted"])

    check("expiry_cutoff is retention_days before today", expiry_cutoff(dt.date(2026, 9, 27), 30) == dt.date(2026, 8, 28))
    check("connection timeouts are not retried", HTTP.get_adapter("https://example.com").max_retries.connect == 0)

    # A host that never answers must fail after ONE attempt, without also
    # trying the page itself (simulated - no real network used).
    calls = []
    real_get = HTTP.get

    def dead_host(*args, **kwargs):
        calls.append(args[0])
        raise requests.ConnectTimeout("simulated")

    HTTP.get = dead_host
    try:
        result = process_source({"id": "x", "name": "Dead", "url": "https://dead.example/events"}, None, today)
    finally:
        HTTP.get = real_get
    check("unreachable host is classed as a timeout", result[0] == "failed_timeout")
    check("unreachable host is tried once, not again for the page", len(calls) == 1)

    class BrokenDB:
        def table(self, name):
            raise RuntimeError("table not found (simulated)")

    check("save_events reports a failure instead of hiding it", "simulated" in (save_events(BrokenDB(), [{"a": 1}]) or ""))
    check("check_events_table reports a missing table", "simulated" in (check_events_table(BrokenDB()) or ""))

    prompt = build_prompt({"name": "Test"}, "https://x.org/events", "CONTENT HERE", today)
    check("build_prompt includes today's date", "2026-09-27" in prompt)
    check("build_prompt includes the page content", "CONTENT HERE" in prompt)

    def slow():
        time.sleep(0.3)
        return "done"
    check("call_with_timeout returns a fast result", call_with_timeout(lambda: "fast", 5) == "fast")
    timed_out = False
    try:
        call_with_timeout(slow, 0.05)
    except RuntimeError as exc:
        timed_out = "timed out" in str(exc)
    check("call_with_timeout enforces its deadline", timed_out)

    for name in ("SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY"):
        present = bool(os.environ.get(name))
        print(f"  [{'ok' if present else 'warn'}] {name} secret is set" if present else f"  [warn] {name} secret is NOT set (fine for self-test, required for a real run)")

    if failures:
        print(f"\nSelf-test FAILED: {len(failures)} check(s) did not pass:")
        for f in failures:
            print(f"  - {f}")
        return False
    print("\nSelf-test passed.")
    return True


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    if "--self-test" in sys.argv:
        sys.exit(0 if self_test() else 1)

    missing = [n for n in ("SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY") if not os.environ.get(n)]
    if missing:
        print("Setup problem: these GitHub secrets are missing or empty: " + ", ".join(missing))
        sys.exit(1)

    supabase_url = os.environ["SUPABASE_URL"].strip().strip("\"'").rstrip("/")
    supabase_key = os.environ["SUPABASE_KEY"].strip().strip("\"'")
    if not re.fullmatch(r"https://[A-Za-z0-9-]+\.supabase\.co", supabase_url):
        print("Setup problem: the SUPABASE_URL secret does not look right.")
        print("It should look like  https://abcdefghijklmnop.supabase.co  (nothing after it).")
        print(f"What the worker received starts with: {supabase_url[:8]!r} and is {len(supabase_url)} characters long.")
        sys.exit(1)

    from supabase import create_client
    db = create_client(supabase_url, supabase_key)

    table_problem = check_events_table(db)
    if table_problem:
        print(f"Setup problem: the events table '{EVENTS_TABLE}' cannot be read: {table_problem}")
        print("Check that the table exists in Supabase (run events_schema.sql) and is in the 'public' schema.")
        if DRY_RUN:
            print("Continuing because this is a dry run - nothing will be saved, and expired-event clean-up cannot be previewed.\n")
        else:
            print("Stopping before any website is read, so nothing is marked as done without being saved.")
            sys.exit(1)

    extract = make_gemini_caller()
    today = today_uk()

    query = db.table("sources").select("*").eq("active", True)
    if CATEGORY_FILTER:
        query = query.in_("category", CATEGORY_FILTER)
    sources = query.execute().data or []
    # Never-checked sources first, then the ones checked longest ago.
    sources.sort(key=lambda s: s.get("last_checked_at") or "")
    if LIMIT > 0:
        sources = sources[:LIMIT]

    which = ", ".join(CATEGORY_FILTER) if CATEGORY_FILTER else "all categories"
    print(f"Today (UK): {today}. Categories: {which}. Fetch engine: {FETCH_ENGINE}. "
          f"Sources to process: {len(sources)}. Dry run: {DRY_RUN}. Model: {MODEL}. "
          f"Run budget: {MAX_RUN_MINUTES} min. Gemini timeout: {GEMINI_TIMEOUT_SECONDS}s.")

    # Everything the summary needs is created here, before the loop, so a
    # crash partway through the loop still leaves a valid report to print.
    totals = {}
    total_events = 0
    zero_event_sources = []
    run_stats = {
        "extracted": 0, "kept": 0, "invalid": 0, "no_date": 0, "event_finished": 0,
        "event_too_far_in_future": 0, "low_relevance": 0, "not_parent_activity": 0,
        "missing_family_evidence": 0, "low_confidence": 0, "duplicates": 0,
    }
    start_time = time.monotonic()
    stopped_early = False
    fatal = None
    processed = 0
    expired_note = "not run"

    try:
        for number, source in enumerate(sources, start=1):
            elapsed_minutes = (time.monotonic() - start_time) / 60
            if elapsed_minutes >= MAX_RUN_MINUTES:
                remaining = len(sources) - processed
                print(f"\nRun budget of {MAX_RUN_MINUTES} min reached after {processed} source(s); "
                      f"stopping cleanly. {remaining} source(s) not yet checked this run - "
                      f"they're the oldest-checked, so next run picks them up first.")
                stopped_early = True
                break

            label = f"[{number}/{len(sources)}] {source['name']}"
            now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
            update = {"last_checked_at": now_iso}
            t0 = time.perf_counter()

            try:
                status, rows, new_hash, message, stats = process_source(source, extract, today)
            except FatalError as exc:
                fatal = exc
                break
            except Exception as exc:
                status, rows, new_hash, message, stats = (
                    "failed_unexpected", [], None, f"{type(exc).__name__}: {exc}", {},
                )

            if status == "ok" and rows and not DRY_RUN:
                save_error = save_events(db, rows)
                if save_error:
                    status = "failed_save"
                    message = f"could not save events ({save_error})"
                    rows = []

            elapsed = time.perf_counter() - t0
            processed += 1
            totals[status] = totals.get(status, 0) + 1
            for key in run_stats:
                run_stats[key] += stats.get(key, 0)

            print(f"{label}: {status.upper()} - {message} ({elapsed:.1f}s)")

            if status in ("ok", "ok_zero"):
                update.update({
                    "last_hash": new_hash, "last_success_at": now_iso, "fail_count": 0,
                    "last_error": None, "last_event_count": len(rows),
                })
                total_events += len(rows)
                if status == "ok_zero":
                    zero_event_sources.append(source["name"])
                if DRY_RUN:
                    for row in rows[:5]:
                        print(f"      would save: {row['start_date']} | {row['title']} | {row['location']}")
                    for sample in stats.get("missing_family_evidence_samples", []):
                        print(f"      would REJECT (no family evidence): {sample}")
                    for sample in stats.get("low_relevance_samples", []):
                        print(f"      would reject (low relevance): {sample}")
            elif status != "unchanged":
                update.update({"fail_count": (source.get("fail_count") or 0) + 1, "last_error": str(message)[:500]})
            else:
                update.update({"fail_count": 0, "last_error": None})

            if not DRY_RUN:
                try:
                    db.table("sources").update(update).eq("id", source["id"]).execute()
                except Exception as exc:
                    print(f"      warning: could not update this source's status ({type(exc).__name__}: {exc})")

            time.sleep(PAUSE_SECONDS)

        if fatal is None:
            try:
                removed = remove_expired_events(db, today)
                if removed is None:
                    expired_note = "clean-up switched off (EXPIRED_RETENTION_DAYS is negative)"
                else:
                    verb = "would be removed" if DRY_RUN else "removed"
                    expired_note = f"{removed} event(s) {verb} (ended more than {EXPIRED_RETENTION_DAYS} days ago)"
            except Exception as exc:
                expired_note = f"clean-up failed ({type(exc).__name__}: {exc})"
    finally:
        total_minutes = (time.monotonic() - start_time) / 60
        print("\n=== Summary ===")
        print(f"Ran for {total_minutes:.1f} min. Sources processed: {processed}/{len(sources)}"
              + (" (stopped early on the time budget)" if stopped_early else ""))
        print(f"Saved/updated events: {total_events}" + (" (dry run - nothing was saved)" if DRY_RUN else ""))
        print("Sources: " + ", ".join(f"{k}={v}" for k, v in sorted(totals.items())))
        print("Events: " + ", ".join(f"{k}={v}" for k, v in run_stats.items()))
        print(f"Expired events: {expired_note}")
        if zero_event_sources:
            print("Worked but found 0 events (worth a look): " + "; ".join(zero_event_sources))

    if fatal is not None:
        print(f"\nSTOPPING THE WHOLE RUN - fatal error: {fatal}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print(f"FATAL WORKER ERROR: {type(exc).__name__}: {exc}")
        sys.exit(1)

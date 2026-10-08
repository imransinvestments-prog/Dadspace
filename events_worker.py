#!/usr/bin/env python3
"""Dadspace Events + Activities quality wrapper.

worker.py continues to own fetching, source selection, retries, Gemini metrics and
Supabase writes.  This wrapper changes the extraction schema and cleaning rules
without adding an extra Gemini call.
"""

from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import json
import os
import re
import time
from urllib.parse import urljoin

import requests

import worker as base

_ORIGINAL_BUILD_PROMPT = base.build_prompt
_ORIGINAL_CLEAN_EVENTS = base.clean_events
_ORIGINAL_PROCESS_SOURCE = base.process_source
_ORIGINAL_FETCH_SOURCE_HTML = base.fetch_source_html

SCHEDULE_SIGNAL = re.compile(
    r"\b(?:weekly|every\s+(?:mon|tue|wed|thu|fri|sat|sun)|mondays?|tuesdays?|wednesdays?|"
    r"thursdays?|fridays?|saturdays?|sundays?|term[- ]?time|after school|class(?:es)?|"
    r"lessons?|sessions?|club|course|\d{1,2}(?::\d{2})?\s*(?:am|pm))\b",
    re.I,
)
SCHOOL = re.compile(
    r"\b(?:primary school|secondary school|high school|academy|sixth form|nursery school|"
    r"preparatory school|prep school|college)\b",
    re.I,
)
HOLIDAY_CAMP = re.compile(
    r"\b(?:holiday camp|half[- ]?term camp|summer camp|easter camp|christmas camp|"
    r"school holiday camp|multi[- ]?activity camp|football camp|sports camp|dance camp|"
    r"drama camp|performing arts camp)\b",
    re.I,
)
STREET_ADDRESS = re.compile(
    r"\b\d+[A-Za-z]?\s+.*\b(?:road|rd|street|st|avenue|ave|lane|ln|drive|dr|way|close|"
    r"court|ct|place|pl|crescent|terrace|gardens?|parkway|highway)\b",
    re.I,
)

_ALLOWED_AUDIENCES = {"children", "families", "general", "adults", "unknown"}

_VENUE_DB = None
_VENUE_CACHE: dict[tuple[str, str], str | None] = {}
_POSTCODE_CACHE: dict[str, tuple[float | None, float | None]] = {}


def _normalise_words(value: str | None) -> str:
    text = (value or "").lower()
    text = re.sub(r"&", " and ", text)
    text = re.sub(r"\b(the|a|an)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalise_postcode(value: str | None) -> str:
    text = re.sub(r"\s+", "", (value or "").upper())
    if len(text) >= 5:
        return text[:-3] + " " + text[-3:]
    return text


def _activity_dedupe_key(title: str, venue: str | None) -> str:
    raw = f"activity|{_normalise_words(title)}|{_normalise_words(venue)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _listing_title(title: str | None, venue: str | None) -> str | None:
    """Remove only an exact, redundant venue suffix; retain distinct class names."""
    if not title or not venue:
        return title
    parts = re.split(r"\s+(?:@|at)\s+", title, maxsplit=1, flags=re.I)
    if len(parts) == 2 and _normalise_words(parts[1]) == _normalise_words(venue):
        return parts[0].strip()
    return title


def _event_dedupe_key(row: dict) -> str:
    url = (row.get("event_url") or "").strip().split("#", 1)[0].rstrip("/").lower()
    source_url = (row.get("source_url") or "").strip().split("#", 1)[0].rstrip("/").lower()
    raw = "|".join(
        [
            "event",
            "url:" + url if url and url != source_url else _normalise_words(row.get("title")),
            str(row.get("start_date") or ""),
            _normalise_words(row.get("venue_name") or row.get("location")),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _explicit_age_min(value: str | None) -> int | None:
    if not value:
        return None
    text = value.lower()
    if "all ages" in text or "family" in text:
        return None
    match = re.search(r"\b(\d{1,2})\s*\+", text)
    if match:
        return int(match.group(1))
    match = re.search(r"\b(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\b", text)
    if match:
        return int(match.group(1))
    if "teen" in text:
        return 13
    if "adult" in text:
        return 18
    return None


def _teen_title(title: str) -> bool:
    return bool(re.search(r"\b(?:teen|teenager|adult[- ]?only)\b", title or "", re.I))


def _suspicious_time(value: str | None, title: str, description: str | None) -> bool:
    if not value:
        return False
    context = f"{title} {description or ''}".lower()
    if any(word in context for word in ("overnight", "sunrise", "dawn", "early morning")):
        return False
    if re.search(r"\b0[0-5]:[0-5]\d\b", value):
        return True
    match = re.search(r"\b(1[0-2]|[1-9]):[0-5]\d\s*am\b", value, re.I)
    return bool(match and int(match.group(1)) <= 5)


def _season_conflict(title: str, description: str | None, start: dt.date) -> bool:
    text = f"{title} {description or ''}".lower()
    if "summer" in text and start.month in {10, 11, 12, 1, 2, 3}:
        return True
    if any(word in text for word in ("christmas", "santa", "festive")) and start.month not in {11, 12, 1}:
        return True
    if re.search(r"\bnew year\s+20\d{2}\b", text) and start.month not in {1, 2}:
        return True
    return False


def _venue_client():
    global _VENUE_DB
    if _VENUE_DB is not None:
        return _VENUE_DB
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
    if not url or not key:
        return None
    _VENUE_DB = create_client(url, key)
    return _VENUE_DB


def _postcode_coords(postcode: str | None) -> tuple[float | None, float | None]:
    pc = _normalise_postcode(postcode)
    if not pc:
        return None, None
    if pc in _POSTCODE_CACHE:
        return _POSTCODE_CACHE[pc]
    try:
        response = requests.get(
            "https://api.postcodes.io/postcodes/" + pc.replace(" ", "%20"),
            timeout=10,
            headers={"User-Agent": base.USER_AGENT},
        )
        payload = response.json() if response.ok else {}
        result = payload.get("result") or {}
        coords = (result.get("latitude"), result.get("longitude"))
    except Exception:
        coords = (None, None)
    _POSTCODE_CACHE[pc] = coords
    return coords


def _mark_possible_venue_match(db, venue_id: str, extracted_name: str, page_url: str):
    if base.DRY_RUN:
        return
    reason = f"Possible source match: {extracted_name} ({page_url})"[:500]
    try:
        db.table("venues").update({"review_reason": reason}).eq("id", venue_id).execute()
    except Exception as exc:
        print(f"      venue review flag warning: {type(exc).__name__}: {exc}")


def _resolve_venue(item: dict, page_url: str) -> str | None:
    """Match source-extracted venue fields. Never guesses missing address data."""
    name = base.clean_str(item.get("venue_name"), 300)
    postcode = _normalise_postcode(base.clean_str(item.get("postcode"), 20))
    address = base.clean_str(item.get("venue_address"), 500)
    if not name:
        return None

    cache_key = (_normalise_words(name), postcode)
    if cache_key in _VENUE_CACHE:
        return _VENUE_CACHE[cache_key]

    db = _venue_client()
    if db is None:
        _VENUE_CACHE[cache_key] = None
        return None

    try:
        candidates = []
        if postcode:
            result = db.table("venues").select("id,venue_name,postcode").ilike("postcode", postcode).limit(20).execute()
            candidates = result.data or []

        norm_name = _normalise_words(name)
        exact = next((v for v in candidates if _normalise_words(v.get("venue_name")) == norm_name), None)
        if exact:
            venue_id = str(exact["id"])
            _VENUE_CACHE[cache_key] = venue_id
            return venue_id

        if candidates:
            ranked = sorted(
                (
                    difflib.SequenceMatcher(None, norm_name, _normalise_words(v.get("venue_name"))).ratio(),
                    v,
                )
                for v in candidates
            )
            score, best = ranked[-1]
            if score >= 0.55:
                _mark_possible_venue_match(db, str(best["id"]), name, page_url)
                _VENUE_CACHE[cache_key] = None
                return None

        # Schools may be valid activity locations, but are not automatically added
        # to the public family-venue directory.
        if SCHOOL.search(name):
            _VENUE_CACHE[cache_key] = None
            return None

        has_real_address = bool(postcode or (address and STREET_ADDRESS.search(address)))
        if not has_real_address:
            _VENUE_CACHE[cache_key] = None
            return None

        if base.DRY_RUN:
            _VENUE_CACHE[cache_key] = None
            return None

        lat, lon = _postcode_coords(postcode)
        source_hash = hashlib.sha1(f"{page_url}|{norm_name}|{postcode}".encode()).hexdigest()[:12]
        row = {
            "venue_name": name,
            "address": address,
            "postcode": postcode or None,
            "latitude": lat,
            "longitude": lon,
            "source": "Dadspace event discovery",
            "source_url": f"{page_url}#dadspace-discovered-{source_hash}",
            "discovered_source_url": page_url,
            "discovered_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "discovery_status": "discovered",
            "public_visible": False,
            "review_reason": "New venue discovered from an event/activity source",
        }
        inserted = db.table("venues").insert(row).execute().data or []
        venue_id = str(inserted[0]["id"]) if inserted else None
        _VENUE_CACHE[cache_key] = venue_id
        return venue_id
    except Exception as exc:
        print(f"      venue match warning: {type(exc).__name__}: {exc}")
        _VENUE_CACHE[cache_key] = None
        return None


def build_prompt(source, url, content, today):
    prompt = _ORIGINAL_BUILD_PROMPT(source, url, content, today)
    # Replace the old date-only instruction rather than paying for a second
    # classification call. All new fields come back in this same response.
    prompt = prompt.replace(
        "Only include real, specific events, open days, activities or attractions with a date. Never invent details.",
        "Include real, specific family EVENTS and recurring family ACTIVITIES. Never invent details. Events require a date; activities may be undated.",
    )
    extra = """

EVENTS VS ACTIVITIES (classify EACH ITEM, never classify from the source category):
- listing_type must be either event or activity.
- activity = a regular weekly, repeating or term-time class/session/group/club. It may have no start_date.
- event = a one-off, seasonal or special event. SCHOOL-HOLIDAY CAMPS ARE EVENTS even when they run for several days or repeat during a holiday.
- is_holiday_camp = true only for a genuine school-holiday camp; otherwise false.
- For an activity, put the human schedule copied from the page in schedule_text (for example "Tuesdays 10am, term time"). Do not invent a schedule. start_date/end_date may be null.
- For an event, start_date is mandatory and schedule_text should normally be null.
- category must classify the ITEM itself, not the website/source. Use one concise category from: holiday_camps, sports, swimming, outdoors_nature, film_theatre, arts_crafts, museums_heritage, farms_animals, libraries, baby_toddler, family_days_out, other.

VENUE FIELDS (SOURCE CONTENT ONLY):
- venue_name, venue_address and postcode must come only from the supplied page content. Never infer, complete or guess them.
- Keep location too for display, but do not fabricate a fuller address.

QUALITY:
- If the supplied content gives a price, ticket cost, admission charge, 'from £X', per-child cost, or says free, copy that concise information into cost_text. If no price appears, cost_text must be null; never guess.
- Distinguish AM from PM carefully. Do not assign overnight/early-morning times unless explicitly supported.
- Do not attach generic page dates that contradict seasonal wording.
- Teen-only and adult-only sessions are not Dadspace family listings unless clearly parent-and-child/family.
- A title explicitly saying teen/teenager should not be treated as a younger family activity merely because its numerical age starts at 12.
"""
    return prompt.replace("\nCONTENT:\n", extra + "\nCONTENT:\n", 1)


def make_gemini_caller():
    """Same Gemini call/metrics as worker.py, with the expanded one-pass schema."""
    from google import genai
    from google.genai import types
    from pydantic import BaseModel
    from typing import Optional

    class ListingSchema(BaseModel):
        title: str
        description: Optional[str]
        listing_type: str
        is_holiday_camp: bool = False
        category: Optional[str] = None
        start_date: Optional[str]
        end_date: Optional[str]
        schedule_text: Optional[str] = None
        time_text: Optional[str]
        location: Optional[str]
        venue_name: Optional[str] = None
        venue_address: Optional[str] = None
        postcode: Optional[str] = None
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
        raise base.FatalError("GEMINI_API_KEY is missing")

    client = genai.Client(api_key=api_key)
    metrics = {
        "api_attempts": 0,
        "input_chars_sent": 0,
        "prompt_tokens": 0,
        "output_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
    }

    def call(prompt):
        last_error = None
        for attempt in range(3):
            try:
                def do_call():
                    metrics["api_attempts"] += 1
                    metrics["input_chars_sent"] += len(prompt)
                    return client.models.generate_content(
                        model=base.MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=list[ListingSchema],
                            temperature=0,
                            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                        ),
                    )

                response = base.call_with_timeout(do_call, base.GEMINI_TIMEOUT_SECONDS)
                usage = getattr(response, "usage_metadata", None)
                if usage is not None:
                    metrics["prompt_tokens"] += int(getattr(usage, "prompt_token_count", 0) or 0)
                    thinking = int(getattr(usage, "thoughts_token_count", 0) or 0)
                    metrics["thinking_tokens"] += thinking
                    metrics["output_tokens"] += int(getattr(usage, "candidates_token_count", 0) or 0) + thinking
                    metrics["total_tokens"] += int(getattr(usage, "total_token_count", 0) or 0)
                data = json.loads(response.text)
                if not isinstance(data, list):
                    raise ValueError("Gemini did not return a list")
                return data
            except Exception as exc:
                text = str(exc)
                if any(word in text for word in ("NOT_FOUND", "PERMISSION_DENIED", "UNAUTHENTICATED", "API key not valid")):
                    raise base.FatalError(f"Gemini rejected the request ({text[:300]})") from exc
                last_error = exc
                time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"Gemini failed after 3 tries: {last_error}")

    call.metrics = metrics
    return call


def _activity_row(item: dict, source: dict, page_url: str, method: str, stats: dict) -> dict | None:
    title = base.clean_str(item.get("title"), 300)
    if not title:
        stats["invalid"] = stats.get("invalid", 0) + 1
        return None

    try:
        relevance = int(item.get("family_relevance") or 0)
    except (TypeError, ValueError):
        relevance = 0
    if relevance < base.MIN_RELEVANCE:
        stats["low_relevance"] = stats.get("low_relevance", 0) + 1
        return None

    audience = base.normalise_text(item.get("audience"))
    if audience not in _ALLOWED_AUDIENCES:
        audience = "unknown"
    family_evidence = base.clean_str(item.get("family_evidence"), 500)
    if audience == "adults" or _teen_title(title):
        stats["teen_or_adult_only"] = stats.get("teen_or_adult_only", 0) + 1
        return None
    if audience not in ("children", "families") and not family_evidence:
        stats["missing_family_evidence"] = stats.get("missing_family_evidence", 0) + 1
        return None

    min_age = _explicit_age_min(base.clean_str(item.get("age_range"), 100))
    if min_age is not None and min_age >= 13:
        stats["teen_or_adult_only"] = stats.get("teen_or_adult_only", 0) + 1
        return None

    try:
        confidence = float(item.get("confidence") or 0)
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence < base.MIN_CONFIDENCE:
        stats["low_confidence"] = stats.get("low_confidence", 0) + 1
        return None

    venue_name = base.clean_str(item.get("venue_name"), 300)
    location = base.clean_str(item.get("location"), 300) or venue_name
    schedule = base.clean_str(item.get("schedule_text"), 300) or base.clean_str(item.get("time_text"), 200)
    event_url = base.absolute_url(item.get("event_url"), page_url)
    if not location:
        stats["missing_activity_location"] = stats.get("missing_activity_location", 0) + 1
        return None
    if not event_url:
        stats["missing_activity_url"] = stats.get("missing_activity_url", 0) + 1
        return None
    # A duration, bare clock time, or 'regular sessions' is not an actionable
    # recurring schedule. Never invent a weekday from the source's location.
    if not schedule or not re.search(
        r"\b(?:mon(?:day)?s?|tue(?:sday)?s?|wed(?:nesday)?s?|thu(?:rsday)?s?|fri(?:day)?s?|sat(?:urday)?s?|sun(?:day)?s?|daily|weekly|monthly|every day|every week|every month)\b",
        schedule, re.I,
    ):
        stats["missing_activity_schedule"] = stats.get("missing_activity_schedule", 0) + 1
        return None
    venue_id = _resolve_venue(item, page_url)
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    key = _activity_dedupe_key(title, venue_name or location)

    return {
        "source_id": source["id"],
        "title": title,
        "description": base.clean_str(item.get("description"), 1000),
        "listing_type": "activity",
        "is_holiday_camp": False,
        "category": base.clean_str(item.get("category"), 80),
        "start_date": None,
        "end_date": None,
        "schedule_text": schedule,
        "time_text": base.clean_str(item.get("time_text"), 200),
        "location": location,
        "venue_name": venue_name,
        "venue_address": base.clean_str(item.get("venue_address"), 500),
        "postcode": _normalise_postcode(base.clean_str(item.get("postcode"), 20)) or None,
        "venue_id": venue_id,
        "event_url": event_url,
        "cost_text": base.clean_str(item.get("cost_text"), 200),
        "age_range": base.clean_str(item.get("age_range"), 100),
        "recurrence": "recurring",
        "family_relevance": max(1, min(5, relevance)),
        "confidence": max(0.0, min(1.0, confidence)),
        "source_url": page_url,
        "extraction_method": method,
        "dedupe_key": key,
        "last_verified_at": now_iso,
        "last_seen_at": now_iso,
    }


def clean_events(raw_events, source, page_url, method, today, stats=None):
    stats = stats if stats is not None else {}
    event_raw = []
    activities = []

    for item in raw_events:
        if not isinstance(item, dict):
            event_raw.append(item)
            continue
        item = dict(item)
        item["title"] = _listing_title(item.get("title"), item.get("venue_name"))
        title_text = f"{item.get('title') or ''} {item.get('description') or ''}"
        holiday = bool(item.get("is_holiday_camp")) or bool(HOLIDAY_CAMP.search(title_text))
        listing_type = str(item.get("listing_type") or "event").strip().lower()
        if holiday:
            item["listing_type"] = "event"
            item["is_holiday_camp"] = True
            item["category"] = "holiday_camps"
            event_raw.append(item)
        elif listing_type == "activity":
            activities.append(item)
        else:
            item["listing_type"] = "event"
            event_raw.append(item)

    # Reuse the established dated-event validation for actual Events.
    event_rows = _ORIGINAL_CLEAN_EVENTS(event_raw, source, page_url, method, today, stats)
    raw_lookup: dict[tuple[str, str], dict] = {}
    for item in event_raw:
        if isinstance(item, dict):
            raw_lookup[(str(item.get("title") or "").strip(), str(item.get("start_date") or "")[:10])] = item

    kept: dict[str, dict] = {}
    for row in event_rows:
        item = raw_lookup.get((str(row.get("title") or "").strip(), str(row.get("start_date") or "")[:10]), {})
        title = row.get("title") or ""
        description = row.get("description")
        start = base.parse_date(row.get("start_date"))

        if start and _season_conflict(title, description, start):
            stats["season_date_conflict"] = stats.get("season_date_conflict", 0) + 1
            continue
        min_age = _explicit_age_min(row.get("age_range"))
        if _teen_title(title) or (min_age is not None and min_age >= 13):
            stats["teen_or_adult_only"] = stats.get("teen_or_adult_only", 0) + 1
            continue
        if _suspicious_time(row.get("time_text"), title, description):
            row["time_text"] = None
            stats["suspicious_time_cleared"] = stats.get("suspicious_time_cleared", 0) + 1

        venue_name = base.clean_str(item.get("venue_name"), 300)
        row.update(
            {
                "listing_type": "event",
                "is_holiday_camp": bool(item.get("is_holiday_camp")),
                "schedule_text": None,
                "category": "holiday_camps" if item.get("is_holiday_camp") else base.clean_str(item.get("category"), 80),
                "venue_name": venue_name,
                "venue_address": base.clean_str(item.get("venue_address"), 500),
                "postcode": _normalise_postcode(base.clean_str(item.get("postcode"), 20)) or None,
                "venue_id": _resolve_venue(item, page_url),
                "last_seen_at": row.get("last_verified_at"),
            }
        )
        row["dedupe_key"] = _event_dedupe_key(row)
        if row["dedupe_key"] in kept:
            stats["duplicates"] = stats.get("duplicates", 0) + 1
            stats["kept"] = max(0, stats.get("kept", 0) - 1)
        else:
            kept[row["dedupe_key"]] = row

    for item in activities:
        stats["extracted"] = stats.get("extracted", 0) + 1
        row = _activity_row(item, source, page_url, method, stats)
        if row is None:
            continue
        key = row["dedupe_key"]
        if key in kept:
            stats["duplicates"] = stats.get("duplicates", 0) + 1
            for field, value in row.items():
                if kept[key].get(field) is None and value is not None:
                    kept[key][field] = value
            if row.get("last_seen_at"):
                kept[key]["last_seen_at"] = row["last_seen_at"]
        else:
            kept[key] = row
            stats["kept"] = stats.get("kept", 0) + 1

    return list(kept.values())


def process_source(source, extract, today):
    # Explicit manual escape hatch for a full re-read. It bypasses only the
    # in-memory hash comparison; DRY_RUN still prevents database writes.
    if os.environ.get("FORCE_REREAD", "false").strip().lower() == "true":
        source = dict(source)
        source["last_hash"] = None
        source["last_success_at"] = None
    return _ORIGINAL_PROCESS_SOURCE(source, extract, today)


def fetch_source_html(source):
    if source.get("source_adapter") == "venue_listing_details":
        from activity_source_discovery import fetch_listing_documents

        # Reviewed static pages can use HTTP even in the browser worker.
        fetch = base.fetch_html_requests if source.get("fetch_method") in {"html", "requests"} else base.fetch_html
        return fetch_listing_documents(source, fetch, base.robots_allows, lambda: time.sleep(base.PAUSE_SECONDS))
    return _ORIGINAL_FETCH_SOURCE_HTML(source)


def install_quality_rules():
    base.build_prompt = build_prompt
    base.clean_events = clean_events
    base.make_gemini_caller = make_gemini_caller
    base.process_source = process_source
    base.fetch_source_html = fetch_source_html

    # Preserve the old date detector but also let clearly scheduled activities
    # through the cheap pre-Gemini gate.
    base.DATE_HINT_PATTERN = re.compile(
        f"(?:{base.DATE_HINT_PATTERN.pattern})|(?:{SCHEDULE_SIGNAL.pattern})",
        base.DATE_HINT_PATTERN.flags | re.I,
    )


def main():
    install_quality_rules()
    return base.main()


if __name__ == "__main__":
    try:
        result = main()
        if isinstance(result, int):
            raise SystemExit(result)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"FATAL EVENT QUALITY WRAPPER ERROR: {type(exc).__name__}: {exc}")
        raise SystemExit(1)

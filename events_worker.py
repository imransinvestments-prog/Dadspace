#!/usr/bin/env python3
"""Dadspace event worker quality wrapper.

The existing worker.py still owns fetching, Gemini extraction and Supabase writes.
This wrapper adds conservative validation and dedupe rules before rows are saved.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
import sys

import worker as base

_ORIGINAL_BUILD_PROMPT = base.build_prompt
_ORIGINAL_CLEAN_EVENTS = base.clean_events
_PROTECTED_RECURRING = re.compile(
    r"\b(weekly|every\s+(?:mon|tue|wed|thu|fri|sat|sun)|term[- ]?time|class|lesson|session|club|course)\b",
    re.I,
)


def _normalise_words(value: str | None) -> str:
    text = (value or "").lower()
    text = re.sub(r"&", " and ", text)
    text = re.sub(r"\b(the|a|an)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _protected_recurring(row: dict) -> bool:
    if (row.get("recurrence") or "").lower() == "recurring":
        return True
    text = f"{row.get('title') or ''} {row.get('description') or ''}"
    return bool(_PROTECTED_RECURRING.search(text))


def _quality_dedupe_key(row: dict) -> str:
    """Conservative cross-source key.

    Recurring sessions deliberately include source_id so weekly classes are never
    merged across sources. One-off/seasonal events can merge only when date AND
    normalised venue/location agree.
    """
    title = _normalise_words(row.get("title"))
    location = _normalise_words(row.get("location"))
    date = str(row.get("start_date") or "")
    if _protected_recurring(row):
        raw = f"recurring|{row.get('source_id')}|{title}|{date}|{location}"
    else:
        raw = f"event|{title}|{date}|{location}"
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


def _suspicious_time(value: str | None, title: str, description: str | None) -> bool:
    if not value:
        return False
    context = f"{title} {description or ''}".lower()
    if any(word in context for word in ("overnight", "sunrise", "dawn", "early morning")):
        return False
    if re.search(r"\b0[0-5]:[0-5]\d\b", value):
        return True
    match = re.search(r"\b(1[0-2]|[1-9]):[0-5]\d\s*am\b", value, re.I)
    if match and int(match.group(1)) <= 5:
        return True
    return False


def _season_conflict(title: str, description: str | None, start: dt.date) -> bool:
    text = f"{title} {description or ''}".lower()
    if "summer" in text and start.month in {10, 11, 12, 1, 2, 3}:
        return True
    if any(word in text for word in ("christmas", "santa", "festive")) and start.month not in {11, 12, 1}:
        return True
    if re.search(r"\bnew year\s+20\d{2}\b", text) and start.month not in {1, 2}:
        return True
    return False


def build_prompt(source, url, content, today):
    prompt = _ORIGINAL_BUILD_PROMPT(source, url, content, today)
    extra = """

ADDITIONAL DADSPACE QUALITY RULES:
- PRICE MATTERS: if the supplied content gives a price, ticket cost, admission charge, 'from £X', per-child cost, or says the event is free, put that exact concise information in cost_text. Do not omit an explicit price. If no price is present, cost_text must be null; never guess.
- TIME SANITY: distinguish AM from PM carefully. Family attractions such as Christmas lights, theatre, museums and daytime activities should not be given overnight/early-morning times unless the source explicitly says so.
- SEASON SANITY: do not attach a generic page date to an event when it contradicts the event wording (for example a Summer camp in October, Christmas event in summer, or 'New Year 2026' outside the New Year period).
- AGE SANITY: teen-only and adult-only sessions are not Dadspace family events. An activity explicitly limited to age 13+ should normally score below 3 unless the source clearly describes it as a parent-and-child/family activity.
- Keep location specific enough to distinguish two different venues. Never reuse a nearby venue from another event.
"""
    return prompt.replace("\nCONTENT:\n", extra + "\nCONTENT:\n", 1)


def clean_events(raw_events, source, page_url, method, today, stats=None):
    stats = stats if stats is not None else {}
    rows = _ORIGINAL_CLEAN_EVENTS(raw_events, source, page_url, method, today, stats)
    kept = []

    for row in rows:
        title = row.get("title") or ""
        description = row.get("description")
        start = base.parse_date(row.get("start_date"))

        if start and _season_conflict(title, description, start):
            stats["season_date_conflict"] = stats.get("season_date_conflict", 0) + 1
            continue

        min_age = _explicit_age_min(row.get("age_range"))
        if min_age is not None and min_age >= 13:
            stats["teen_or_adult_only"] = stats.get("teen_or_adult_only", 0) + 1
            continue

        if _suspicious_time(row.get("time_text"), title, description):
            row["time_text"] = None
            stats["suspicious_time_cleared"] = stats.get("suspicious_time_cleared", 0) + 1

        row["dedupe_key"] = _quality_dedupe_key(row)
        kept.append(row)

    removed = len(rows) - len(kept)
    if removed:
        stats["kept"] = max(0, stats.get("kept", 0) - removed)
    return kept


def install_quality_rules():
    base.build_prompt = build_prompt
    base.clean_events = clean_events


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

#!/usr/bin/env python3
"""Run the Dadspace deals worker using Supabase tables for matching data.

This compatibility entry point keeps the mature deals pipeline in
``deals_worker.py`` while replacing two legacy dependencies:

- CSV relevance lists -> Supabase tables
- retired Gemini 2.5 model -> Gemini 3.8 Flash

Supabase tables used:
- public.parent_discount_items
- public.parent_deal_exclusions
"""

import json
import os
import re
import sys
import time

import requests

import deals_worker as worker


ITEMS_TABLE = "parent_discount_items"
EXCLUSIONS_TABLE = "parent_deal_exclusions"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


def _truthy(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def load_items_from_supabase():
    rows = worker.sb(
        "GET",
        ITEMS_TABLE,
        params={"select": "*", "order": "id"},
    ) or []

    # compile_items() predates the DB tables and expects CSV-style yes/no text.
    for row in rows:
        row["active"] = "yes" if _truthy(row.get("active", True)) else "no"
        row["uk_terms"] = row.get("uk_terms") or ""
        row["display_group"] = row.get("display_group") or ""
        row["tier"] = row.get("tier") or ""
        row["value_band"] = row.get("value_band") or "low"
        row["item_or_service"] = row.get("item_or_service") or ""
    return rows


def load_exclusions_from_supabase():
    rows = worker.sb(
        "GET",
        EXCLUSIONS_TABLE,
        params={"select": "*", "order": "id"},
    ) or []

    # The original exclusion CSV included mode. The DB table may only contain
    # term/reason, so missing modes default to soft.
    for row in rows:
        row["term"] = row.get("term") or ""
        row["reason"] = row.get("reason") or ""
        row["mode"] = (row.get("mode") or "soft").strip().lower()
    return rows


def load_database_list(path):
    """Drop-in replacement for deals_worker.load_csv()."""
    if path == worker.ITEMS_CSV:
        return load_items_from_supabase()
    if path == worker.EXCLUSIONS_CSV:
        return load_exclusions_from_supabase()
    raise RuntimeError(f"Unexpected legacy list path: {path}")


def gemini_classify_38(batch):
    """Gemini 3.8 Flash classifier using the current generateContent config."""
    prompt = (
        "You classify UK shopping deals for Dadspace, an app for dads and parents of "
        "children aged 0 to 12.\n"
        "For each deal decide whether it is a genuinely useful PRODUCT deal for babies, "
        "children up to about 12, or their parents.\n"
        "Reject: pet products, adult-only items, teen (13+) items, second-hand items, "
        "services, tuition, insurance, general groceries (baby food is fine), games "
        "consoles and video games, cleaning products.\n"
        "Return ONLY a JSON array with one object per deal:\n"
        '{"id": <id>, "relevant": true or false, "group": one of '
        + json.dumps(worker.GROUPS)
        + ' or "none", "relevance": 1-5, '
        '"evidence": "a short phrase copied EXACTLY from the deal title that shows it '
        'is for babies, children or parents, or empty string"}\n'
        "relevance 5 = clearly for babies/children/parents, 3 = probably, 1 = not at all.\n\n"
        "Deals:\n"
        + json.dumps(batch, ensure_ascii=False)
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 4096,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{worker.GEMINI_MODEL}:generateContent"
    )

    for attempt in (1, 2):
        try:
            response = requests.post(
                url,
                headers={"x-goog-api-key": worker._GEMINI_KEY},
                json=body,
                timeout=(10, 60),
            )
        except requests.exceptions.RequestException as exc:
            if attempt == 1:
                time.sleep(3)
                continue
            raise RuntimeError(f"Gemini network error: {str(exc)[:150]}") from exc

        if response.status_code in (429, 500, 502, 503) and attempt == 1:
            time.sleep(5)
            continue
        if response.status_code != 200:
            raise RuntimeError(
                f"Gemini HTTP {response.status_code}: {response.text[:200]}"
            )
        break

    data = response.json()
    usage = data.get("usageMetadata", {})
    tokens_in = usage.get("promptTokenCount", 0)
    tokens_out = usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        answers = json.loads(text)
        return (
            {
                int(answer["id"]): answer
                for answer in answers
                if isinstance(answer, dict) and "id" in answer
            },
            tokens_in,
            tokens_out,
        )
    except Exception as exc:
        raise worker.GeminiError(
            f"could not read Gemini answer: {exc}", tokens_in, tokens_out
        ) from exc


def configure_worker():
    worker.load_csv = load_database_list
    worker.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    worker.gemini_classify = gemini_classify_38


def main():
    configure_worker()

    if "--self-test" in sys.argv:
        return 0 if worker.self_test() else 1
    return worker.run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as crash:
        import traceback

        traceback.print_exc()
        if worker._SB_URL and worker._SB_KEY:
            worker.log_run(
                0,
                {
                    "status": "crashed",
                    "error": str(crash)[:300],
                    "model": worker.GEMINI_MODEL,
                    "total_tokens": worker.STATS["tokens_in"] + worker.STATS["tokens_out"],
                },
            )
        sys.exit(1)

#!/usr/bin/env python3
"""Dadspace deals worker entry point.

This layer keeps the mature classification/persistence pipeline in
``deals_worker.py`` while adding database-backed relevance lists, Gemini 3.8
Flash and pluggable deal-source adapters (RSS, Awin, FMTC and Pepper API).
"""

import json
import os
import re
import sys
import time

import requests

import deals_worker as worker
from deals_source_adapters import fetch_source as fetch_adapter_source

ITEMS_TABLE = "parent_discount_items"
EXCLUSIONS_TABLE = "parent_deal_exclusions"
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"


def _truthy(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def load_items_from_supabase():
    rows = worker.sb("GET", ITEMS_TABLE, params={"select": "*", "order": "id"}) or []
    for row in rows:
        row["active"] = "yes" if _truthy(row.get("active", True)) else "no"
        row["uk_terms"] = row.get("uk_terms") or ""
        row["display_group"] = row.get("display_group") or ""
        row["tier"] = row.get("tier") or ""
        row["value_band"] = row.get("value_band") or "low"
        row["item_or_service"] = row.get("item_or_service") or ""
    return rows


def load_exclusions_from_supabase():
    rows = worker.sb("GET", EXCLUSIONS_TABLE, params={"select": "*", "order": "id"}) or []
    for row in rows:
        row["term"] = row.get("term") or ""
        row["reason"] = row.get("reason") or ""
        row["mode"] = (row.get("mode") or "soft").strip().lower()
    return rows


def load_database_list(path):
    if path == worker.ITEMS_CSV:
        return load_items_from_supabase()
    if path == worker.EXCLUSIONS_CSV:
        return load_exclusions_from_supabase()
    raise RuntimeError(f"Unexpected legacy list path: {path}")


def gemini_classify_38(batch):
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
        "Deals:\n" + json.dumps(batch, ensure_ascii=False)
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
            raise RuntimeError(f"Gemini HTTP {response.status_code}: {response.text[:200]}")
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
            {int(a["id"]): a for a in answers if isinstance(a, dict) and "id" in a},
            tokens_in,
            tokens_out,
        )
    except Exception as exc:
        raise worker.GeminiError(
            f"could not read Gemini answer: {exc}", tokens_in, tokens_out
        ) from exc


def get_all_sources():
    return worker.sb(
        "GET",
        "deal_sources",
        params={"select": "*", "order": "id"},
    ) or []


def credential_state(source_type):
    source_type = (source_type or "rss").lower()
    if source_type == "awin":
        return bool(os.getenv("AWIN_API_TOKEN", "").strip() and os.getenv("AWIN_PUBLISHER_ID", "").strip())
    if source_type == "fmtc":
        return bool(os.getenv("FMTC_API_TOKEN", "").strip())
    if source_type in {"pepper", "pepper_api", "hotukdeals_api"}:
        # Pepper may allow an endpoint without a token; URL presence is the
        # minimum configuration requirement and is stored on the source row.
        return None
    return True


def enhanced_details(all_deals, source_results, started, status="ok", error=None):
    details = worker.build_details(all_deals, source_results, started, status=status, error=error)
    details["sources"] = source_results
    details["source_totals"] = {
        "configured": len(source_results),
        "ok": sum(1 for s in source_results if s["status"] == "ok"),
        "empty": sum(1 for s in source_results if s["status"] == "empty"),
        "failed": sum(1 for s in source_results if s["status"] not in ("ok", "empty", "inactive")),
        "items": sum(s.get("items", 0) for s in source_results),
    }
    return details


def self_test():
    ok = True
    if not (worker._SB_URL and worker._SB_KEY):
        worker.log("FAIL Supabase: SUPABASE_URL or key secret is missing")
        return False

    try:
        items = load_items_from_supabase()
        entries = worker.compile_items(items)
        exclusions = worker.compile_exclusions(load_exclusions_from_supabase())
        worker.log(
            f"OK  lists loaded: {len(items)} items, {len(entries)} match terms, "
            f"{len(exclusions)} exclusion terms"
        )
    except Exception as exc:
        worker.log(f"FAIL lists: {exc}")
        ok = False

    try:
        sources = get_all_sources()
        active = [s for s in sources if _truthy(s.get("active"))]
        worker.log(f"OK  Supabase reachable: {len(sources)} sources, {len(active)} active")
        for source in sources:
            stype = (source.get("source_type") or "rss").lower()
            state = "ACTIVE" if _truthy(source.get("active")) else "inactive"
            creds = credential_state(stype)
            credential_note = ""
            if creds is False:
                credential_note = " - credentials missing"
            elif creds is True and stype in {"awin", "fmtc"}:
                credential_note = " - credentials found"
            worker.log(f"  {state:8} {source.get('name')} [{stype}]{credential_note}")
    except Exception as exc:
        worker.log(f"FAIL Supabase sources: {exc}")
        ok = False

    worker.log(
        ("OK  " if worker._GEMINI_KEY else "WARN ")
        + "Gemini key "
        + ("found" if worker._GEMINI_KEY else "missing (unclear items will be skipped)")
    )
    return ok


def run():
    started = worker.now_utc()
    worker.log(
        f"Deals worker starting. {'DRY RUN (nothing will be saved)' if worker.DRY_RUN else 'LIVE RUN'}"
    )
    if not (worker._SB_URL and worker._SB_KEY):
        worker.log("ERROR: SUPABASE_URL / Supabase key secrets are not set in the workflow.")
        return 1

    items = load_items_from_supabase()
    entries = worker.compile_items(items)
    exclusions = worker.compile_exclusions(load_exclusions_from_supabase())
    worker.log(f"Loaded {len(entries)} match terms and {len(exclusions)} exclusion terms")

    configured_sources = get_all_sources()
    sources = [s for s in configured_sources if _truthy(s.get("active"))]
    worker.log(f"{len(sources)} active sources ({len(configured_sources)} configured)")

    all_deals = []
    seen_keys = set()
    source_results = []

    for source in sources:
        source_type = (source.get("source_type") or "rss").lower()
        status, raw_items, info = fetch_adapter_source(source, worker.fetch_source)
        worker.log(
            f"- {source.get('name')} [{source_type}]: {status} "
            f"({len(raw_items)} items) {info}"
        )
        result = {
            "id": source.get("id"),
            "name": source.get("name"),
            "source_type": source_type,
            "status": status,
            "items": len(raw_items),
            "info": info,
        }
        source_results.append(result)

        if not worker.DRY_RUN:
            try:
                worker.update_source_health(source, status)
            except Exception as exc:
                worker.log(f"  (source health not saved: {exc})")

        for raw in raw_items:
            deal = worker.normalise(raw)
            deal.update({"source": source.get("name"), "source_id": source.get("id")})
            why = worker.validate_deal(deal)
            if not why and deal["dedupe_key"] in seen_keys:
                why = "duplicate"
            if why:
                worker.reject(deal, why)
            else:
                seen_keys.add(deal["dedupe_key"])
            all_deals.append(deal)
        if source_type == "rss":
            time.sleep(1.5)

    stats = worker.process_items(
        all_deals,
        entries,
        exclusions,
        gemini_classify_38 if worker._GEMINI_KEY else None,
    )
    kept = [d for d in all_deals if d.get("decision") == "kept"]
    skipped_prefilter = sum(
        1
        for d in all_deals
        if d.get("decision") == "rejected" and worker.stage_of(d["reason"]) == "prefilter"
    )

    worker.write_review(all_deals, source_results, stats, started)
    if worker.DRY_RUN:
        worker.log("\nDRY RUN: nothing was saved. Download the 'deals-dry-run-review' artifact to review.")
    else:
        worker.save_live(kept, {})
        worker.log(
            f"\nLIVE: saved {len(kept)} deals and expired deals not seen for "
            f"{worker.EXPIRE_AFTER_DAYS} days."
        )

    worker.log_run(
        skipped_prefilter,
        enhanced_details(all_deals, source_results, started),
    )
    return 0


def configure_worker():
    worker.load_csv = load_database_list
    worker.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    worker.gemini_classify = gemini_classify_38


def main():
    configure_worker()
    if "--self-test" in sys.argv:
        return 0 if self_test() else 1
    return run()


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

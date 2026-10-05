#!/usr/bin/env python3
"""Enrich the existing news scoring/save path. No additional worker or model call."""
import argparse
import json
import os
import re
import sys
from pathlib import Path

import news_worker as core

GEOGRAPHY = json.loads(Path(__file__).with_name("news_geography.json").read_text())
SCOPES = {"nationwide", "regional", "local"}
GEO_KEYS = ("geo_scope", "geo_region", "admin_area", "locality")
UNKNOWN_GEO = dict.fromkeys(GEO_KEYS)
_geo_by_article = {}
_review = []
_run_stats = None
_self_testing = False

GEO_INSTRUCTIONS = """
Also return geographic metadata for EVERY result, including low-relevance items:
- "geo_scope": nationwide, regional, or local
  nationwide means across the selected UK nation, or UK-wide when region=uk.
  regional means one of the supported English regions below. Otherwise use local
  for a single named council area; do not invent a supported region for a wider area.
  local means one council district/unitary authority or administrative county.
- "geo_region": for regional stories, EXACTLY one of: {regions}; otherwise "".
- "locality": for district/town stories, the official local-authority district or
  unitary-authority name (postcodes.io admin_district), NOT a ward, parish, village
  or unqualified town name. Use it only if the council area is clear; otherwise "".
- "admin_area": for county-wide stories, the official administrative county name.
  It can also be county context for a district story. Leave locality empty ONLY
  when the whole county/authority is affected, not to broaden a town-specific story.
  For a unitary/council-wide story use that authority's name as locality.
Use official names without "Council" suffixes. Glasgow = Glasgow City;
Edinburgh = City of Edinburgh; Bristol = Bristol, City of.
For local stories about towns within larger districts, use the district ONLY when
clear (Stamford = South Kesteven); do not use a ward or infer from the publisher.
General parenting advice, product recalls, and rights affecting the whole selected
nation are nationwide. Clear local news must never be labelled nationwide merely
because its exact council is uncertain: keep local with empty geography in that
case so it is explicitly reported as unclassified. Likewise an unsupported broad
region (e.g. South Wales) stays regional with its named geo_region for review.
Clear place evidence must come from headline, snippet, source or named public body.
Every object must include all four geography fields, using "" for unused fields.
""".replace("{regions}", ", ".join(GEOGRAPHY["regions"]))

_anchor = '- "summary": one plain sentence (max 25 words) in your own words'
if core.PROMPT.count(_anchor) != 1:
    raise RuntimeError("News scoring prompt changed: locality insertion point must be reviewed")
core.PROMPT = core.PROMPT.replace(_anchor, GEO_INSTRUCTIONS + "\n" + _anchor)
core.PROMPT = core.PROMPT.replace(
    '"region": "uk", "summary": "..."',
    '"region": "uk", "geo_scope": "nationwide", "geo_region": "", "admin_area": "", "locality": "", "summary": "..."',
)
_original_gemini_score = core.gemini_score
_original_save_items = core.save_items
_original_log_run = core.log_run

SELF_TEST_CASES = [
    ({"title": "UK-wide recall of a faulty children's car seat",
      "source": "Office for Product Safety and Standards", "snippet": "Recall applies throughout the UK."},
     {"region": "uk", "geo_scope": "nationwide"}),
    ({"title": "School meal eligibility changes across England",
      "source": "Department for Education", "snippet": "The policy applies to schools throughout England."},
     {"region": "england", "geo_scope": "nationwide"}),
    ({"title": "New family support across the East of England",
      "source": "test", "snippet": "The programme applies across the entire East of England region."},
     {"region": "england", "geo_scope": "regional", "geo_region": "east_of_england"}),
    ({"title": "Cambridge City Council opens family play sessions in Cambridge",
      "source": "Cambridge City Council", "snippet": "Only for families in the Cambridge council district, Cambridgeshire."},
     {"region": "england", "geo_scope": "local", "locality": "cambridge"}),
    ({"title": "Cambridgeshire County Council changes school transport across the county",
      "source": "Cambridgeshire County Council", "snippet": "A county-wide policy for every district in Cambridgeshire; no single town."},
     {"region": "england", "geo_scope": "local", "admin_area": "cambridgeshire", "locality": None}),
    ({"title": "Glasgow City Council changes children's library opening hours",
      "source": "Glasgow City Council", "snippet": "Applies only to Glasgow City Council libraries."},
     {"region": "scotland", "geo_scope": "local", "locality": "glasgow_city"}),
    ({"title": "Cardiff Council opens free family play sessions",
      "source": "Cardiff Council", "snippet": "Sessions only for residents of Cardiff."},
     {"region": "wales", "geo_scope": "local", "locality": "cardiff"}),
    ({"title": "Belfast City Council offers free school holiday play sessions",
      "source": "Belfast City Council", "snippet": "For Belfast council area residents only."},
     {"region": "northern_ireland", "geo_scope": "local", "locality": "belfast"}),
]


def slug(value):
    if not isinstance(value, str) or re.search(r"\(pseudo\)|unparished area", value, re.I):
        return None
    token = re.sub(r"[^a-z0-9]+", "_", value.strip().lower().replace("&", " and ")).strip("_")
    return token if token and len(token) <= 100 else None


def area(value):
    token = slug(value)
    if not token:
        return None
    token = re.sub(r"_(?:county_council|district_council|borough_council|city_council|council)$", "", token)
    return GEOGRAPHY["areaAliases"].get(token, token)


def geo_region(value):
    token = slug(value)
    token = GEOGRAPHY["regionAliases"].get(token, token)
    return token if token in GEOGRAPHY["regions"] else None


def raw_geo_problem(result):
    """Validate actual returned fields BEFORE supplying any defaults."""
    if not isinstance(result, dict):
        return "result is not an object"
    if result.get("region") not in core.REGIONS:
        return "missing/invalid nation"
    if any(key not in result for key in GEO_KEYS):
        return "missing geography fields"
    if result.get("geo_scope") not in SCOPES:
        return "missing/invalid geo_scope"
    if any(result[key] is not None and not isinstance(result[key], str) for key in GEO_KEYS[1:]):
        return "geography fields must be strings or null"
    scope = result["geo_scope"]
    if scope != "nationwide" and result["region"] == "uk":
        return "UK-wide nation conflicts with narrow scope"
    if scope == "regional" and (result["region"] != "england" or not geo_region(result["geo_region"])):
        return "unsupported/missing sub-national region"
    if scope == "local" and not (area(result["admin_area"]) or area(result["locality"])):
        return "local scope without usable council/county"
    return None


def normalise_geo(result):
    if raw_geo_problem(result):
        # Keep legacy behaviour without falsely recording local news as nationwide.
        return UNKNOWN_GEO.copy()
    scope = result["geo_scope"]
    return {
        "geo_scope": scope,
        "geo_region": geo_region(result["geo_region"]) if scope == "regional" else None,
        "admin_area": area(result["admin_area"]) if scope == "local" else None,
        "locality": area(result["locality"]) if scope == "local" else None,
    }


def gemini_score_with_geo(batch):
    if _self_testing:
        batch = [dict(item, i=i) for i, (item, _) in enumerate(SELF_TEST_CASES)]
    results = _original_gemini_score(batch)
    seen = set()
    for result in results:
        try:
            index = int(result["i"])
            if not 0 <= index < len(batch) or index in seen:
                continue
            item = batch[index]
            seen.add(index)
        except (ValueError, TypeError, KeyError):
            continue
        problem = raw_geo_problem(result)
        geo = normalise_geo(result)
        _geo_by_article[(item.get("title", ""), item.get("source", ""))] = geo
        review = {
            "stage": "self-test" if _self_testing else "collection",
            "i": index, "title": item.get("title"), "source": item.get("source"),
            "region": result.get("region"), "raw": {key: result.get(key) for key in GEO_KEYS},
            "normalised": geo, "warning": problem,
        }
        _review.append(review)
        if core.DRY_RUN or _self_testing:
            print("NEWS GEOGRAPHY " + json.dumps(review, ensure_ascii=False))
    if len(seen) != len(batch):
        _review.append({"stage": "self-test" if _self_testing else "collection",
                        "warning": "missing/duplicate/out-of-range article results",
                        "expected": len(batch), "received": len(seen)})
    return results


def save_items_with_geo(rows):
    for row in rows:
        row.update(_geo_by_article.get(
            (row.get("title", ""), row.get("source_name", "")), UNKNOWN_GEO))
    return _original_save_items(rows)


def log_run_with_geo(stats, worker="news", dry_run=None):
    global _run_stats
    _run_stats = stats.copy()
    classified = [r for r in _review if r.get("normalised", {}).get("geo_scope")]
    unknown = sum(bool(r.get("warning")) for r in _review)
    print(f"Locality review: {len(classified)} classified; {unknown} warnings/unclassified")
    _original_log_run(stats, worker=worker, dry_run=dry_run)


def write_review():
    path = os.environ.get("NEWS_LOCALITY_REPORT_PATH")
    if path:
        with open(path, "a", encoding="utf-8") as out:
            for row in _review:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")


core.gemini_score = gemini_score_with_geo
core.save_items = save_items_with_geo
core.log_run = log_run_with_geo


def self_test():
    global _self_testing
    _review.clear()
    _geo_by_article.clear()
    _self_testing = True
    try:
        rc = core.self_test()  # Same existing scoring call, now tests representative geography.
    finally:
        _self_testing = False
    if rc:
        return rc
    try:
        columns = ",".join(GEO_KEYS)
        core.sb("GET", "news_items", params={"select": columns, "limit": "1"})
        core.sb("GET", "feed_items", params={"select": columns, "limit": "1"})
    except Exception as exc:
        print(f"SELF-TEST FAILED: locality schema/view unavailable: {exc}")
        return 1
    problems = [row["warning"] for row in _review if row.get("warning")]
    actual = {row["i"]: row for row in _review if "normalised" in row}
    for i, (_, expected) in enumerate(SELF_TEST_CASES):
        row = actual.get(i)
        if not row:
            problems.append(f"missing geography self-test case {i}")
            continue
        values = {"region": row["region"], **row["normalised"]}
        for key, value in expected.items():
            if values.get(key) != value:
                problems.append(f"case {i}: {key} expected {value!r}, got {values.get(key)!r}")
    if problems:
        print("SELF-TEST FAILED:\n  " + "\n  ".join(problems))
        return 1
    print(f"news locality metadata: OK ({len(SELF_TEST_CASES)} representative cases)")
    return 0


def run():
    global _run_stats
    _run_stats = None
    _review.clear()
    _geo_by_article.clear()
    core.run()
    # The core logs a failed batch but returns normally. Make this review gate visible.
    if core.DRY_RUN and (_run_stats is None or _run_stats.get("batches_failed")):
        return 1
    if not _run_stats.get("scored"):
        print("No new articles scored; inspect the self-test sample for classification evidence.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.self_test:
            rc = self_test()
        elif not (core.SUPABASE_URL and core.SUPABASE_SERVICE_KEY and core.GEMINI_API_KEY):
            print("Missing SUPABASE_URL, SUPABASE_SERVICE_KEY or GEMINI_API_KEY")
            rc = 1
        else:
            rc = run()
    finally:
        write_review()
    sys.exit(rc)

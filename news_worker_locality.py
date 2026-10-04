#!/usr/bin/env python3
"""Locality-aware entrypoint for the existing Dadspace news worker.

This deliberately keeps news_worker.py unchanged. It enriches the worker's existing
Gemini scoring response with geographic metadata and adds those fields to rows just
before the existing save_items() function writes them. No extra Gemini call, worker,
or schedule is introduced.
"""

import argparse
import re
import sys

import news_worker as core

SCOPES = {"nationwide", "regional", "local"}
_geo_by_article = {}

GEO_INSTRUCTIONS = """
Also classify geographic scope. Be conservative: do not invent a place that is not
clear from the headline, snippet, source, or named public body.
- "geo_scope": one of nationwide, regional, local
    * nationwide = applies across the selected "region" above. For region=uk this
      means UK-wide; for region=england it means broadly across England, etc.
    * regional = applies to a broad sub-national English/Scottish/Welsh/NI region
      such as East of England, North West, Highlands, South Wales. Do not use this
      merely because the publisher is regional.
    * local = mainly matters to one town, city, county, council or local-authority area.
- "geo_region": broad sub-national region when geo_scope=regional, otherwise "".
- "admin_area": county/council/local-authority area when clearly stated for local
  stories, otherwise "".
- "locality": town/city/locality when clearly stated for local stories, otherwise "".
For product recalls, national employment rights, general parenting advice and other
stories not tied to a particular place, use nationwide. If geographic detail is
uncertain, prefer nationwide over guessing a local place.
"""

# Extend the existing scoring prompt without altering its relevance/category rules.
core.PROMPT = core.PROMPT.replace(
    '- "summary": one plain sentence (max 25 words) in your own words',
    GEO_INSTRUCTIONS + '\n- "summary": one plain sentence (max 25 words) in your own words',
)

_original_gemini_score = core.gemini_score
_original_save_items = core.save_items


def slug(value):
    value = str(value or "").strip().lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value[:100] or None


def normalise_geo(result):
    region = str(result.get("region", "uk")).strip().lower().replace(" ", "_")
    if region not in core.REGIONS:
        region = "uk"

    scope = str(result.get("geo_scope", "nationwide")).strip().lower()
    if scope not in SCOPES:
        scope = "nationwide"

    geo_region = slug(result.get("geo_region"))
    admin_area = slug(result.get("admin_area"))
    locality = slug(result.get("locality"))

    # UK-wide stories cannot also be geographically local in our matching model.
    if region == "uk":
        return {"geo_scope": "nationwide", "geo_region": None, "admin_area": None, "locality": None}

    # Never hide a story because the model claimed a narrow scope but supplied no
    # usable place. Falling back to nationwide is deliberately conservative.
    if scope == "regional" and not geo_region:
        scope = "nationwide"
    if scope == "local" and not (admin_area or locality):
        scope = "nationwide"

    if scope == "nationwide":
        geo_region = admin_area = locality = None
    elif scope == "regional":
        admin_area = locality = None
    else:  # local
        geo_region = None

    return {
        "geo_scope": scope,
        "geo_region": geo_region,
        "admin_area": admin_area,
        "locality": locality,
    }


def gemini_score_with_geo(batch):
    results = _original_gemini_score(batch)
    for result in results:
        try:
            item = batch[int(result["i"])]
        except Exception:
            continue
        geo = normalise_geo(result)
        _geo_by_article[(item.get("title", ""), item.get("source", ""))] = geo
    return results


def save_items_with_geo(rows):
    for row in rows:
        geo = _geo_by_article.get((row.get("title", ""), row.get("source_name", "")))
        if geo:
            row.update(geo)
        else:
            # Safe fallback if a batch returned malformed geography.
            row.update({"geo_scope": "nationwide", "geo_region": None, "admin_area": None, "locality": None})
    return _original_save_items(rows)


core.gemini_score = gemini_score_with_geo
core.save_items = save_items_with_geo


def self_test():
    rc = core.self_test()
    if rc:
        return rc
    # The core self-test calls the patched scorer once. Confirm we captured valid
    # locality metadata from that same scoring call.
    if not _geo_by_article:
        print("SELF-TEST FAILED:\n  locality metadata was not returned by Gemini")
        return 1
    invalid = [g for g in _geo_by_article.values() if g.get("geo_scope") not in SCOPES]
    if invalid:
        print("SELF-TEST FAILED:\n  invalid geo_scope returned")
        return 1
    print("news locality metadata: OK")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if not (core.SUPABASE_URL and core.SUPABASE_SERVICE_KEY and core.GEMINI_API_KEY):
        print("Missing SUPABASE_URL, SUPABASE_SERVICE_KEY or GEMINI_API_KEY")
        sys.exit(1)
    core.run()

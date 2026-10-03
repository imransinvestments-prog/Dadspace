#!/usr/bin/env python3
"""Dadspace canonical venue reference worker.

Responsibilities:
- ingest authoritative/reference venue datasets (Sport England, library data)
- match against public.venues BEFORE inserting anything
- enrich provenance through public.venue_sources
- never make newly discovered venues public automatically

The worker is adapter-driven. Each source can be activated independently in
public.sources once its data-access route is configured and verified.
"""

from __future__ import annotations

import csv
import difflib
import io
import json
import math
import os
import re
from dataclasses import dataclass
from typing import Iterable

import requests
from supabase import create_client

DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"
LIMIT = int(os.environ.get("LIMIT", "0") or 0)
UA = os.environ.get("USER_AGENT", "Mozilla/5.0 (compatible; DadspaceVenueBot/1.0)")


def norm_name(value: str | None) -> str:
    text = (value or "").lower().replace("&", " and ")
    text = re.sub(r"\b(the|a|an)\b", " ", text)
    text = re.sub(r"\b(ltd|limited|plc)\b", " ", text)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def norm_postcode(value: str | None) -> str:
    text = re.sub(r"\s+", "", (value or "").upper())
    return (text[:-3] + " " + text[-3:]) if len(text) >= 5 else text


def distance_m(a_lat, a_lon, b_lat, b_lon) -> float | None:
    if None in (a_lat, a_lon, b_lat, b_lon):
        return None
    r = 6371000.0
    p1, p2 = math.radians(float(a_lat)), math.radians(float(b_lat))
    dp = math.radians(float(b_lat) - float(a_lat))
    dl = math.radians(float(b_lon) - float(a_lon))
    q = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(q), math.sqrt(1 - q))


@dataclass
class Candidate:
    source_name: str
    source_record_id: str
    source_url: str | None
    venue_name: str
    postcode: str | None = None
    address: str | None = None
    town_city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    category: str | None = None
    website: str | None = None
    operator: str | None = None
    payload: dict | None = None


def db_client():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY/SERVICE_KEY are required")
    return create_client(url, key)


def get_json_or_csv(url: str):
    r = requests.get(url, timeout=60, headers={"User-Agent": UA, "Accept": "application/json,text/csv,*/*"})
    r.raise_for_status()
    ctype = (r.headers.get("content-type") or "").lower()
    if "json" in ctype or r.text.lstrip().startswith(("[", "{")):
        return r.json()
    return list(csv.DictReader(io.StringIO(r.text)))


def first(row: dict, *keys):
    lowered = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        if key.lower() in lowered and lowered[key.lower()] not in (None, ""):
            return lowered[key.lower()]
    return None


def as_float(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def rows_from_payload(payload) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("results", "data", "items", "features", "sites", "libraries"):
            value = payload.get(key)
            if isinstance(value, list):
                if key == "features":
                    rows = []
                    for f in value:
                        if not isinstance(f, dict):
                            continue
                        row = dict(f.get("properties") or {})
                        coords = ((f.get("geometry") or {}).get("coordinates") or [])
                        if len(coords) >= 2:
                            row.setdefault("longitude", coords[0])
                            row.setdefault("latitude", coords[1])
                        rows.append(row)
                    return rows
                return [x for x in value if isinstance(x, dict)]
    return []


def active_places_candidates(source: dict) -> Iterable[Candidate]:
    # Prefer a configured official API/download URL; the portal page itself is
    # deliberately not scraped because it is not the dataset.
    url = os.environ.get("ACTIVE_PLACES_DATA_URL", "").strip()
    if not url:
        raise RuntimeError("ACTIVE_PLACES_DATA_URL not configured")
    payload = get_json_or_csv(url)
    for row in rows_from_payload(payload) if not isinstance(payload, list) else payload:
        name = first(row, "site_name", "sitename", "name", "facility_name")
        record_id = first(row, "site_id", "siteid", "id", "uprn")
        if not name or not record_id:
            continue
        yield Candidate(
            source_name=source["name"], source_record_id=str(record_id),
            source_url=source.get("url"), venue_name=str(name),
            postcode=norm_postcode(first(row, "postcode", "post_code")) or None,
            address=first(row, "address", "full_address", "site_address"),
            town_city=first(row, "town", "city", "locality"),
            latitude=as_float(first(row, "latitude", "lat")),
            longitude=as_float(first(row, "longitude", "lng", "lon")),
            category="sports_facility", website=first(row, "website", "url"),
            operator=first(row, "operator", "operator_name"), payload=row,
        )


def library_candidates(source: dict) -> Iterable[Candidate]:
    # The schema is not itself a live national feed. Configure one or more
    # conforming feeds as comma-separated URLs when available.
    raw = os.environ.get("LIBRARY_DATA_URLS", "").strip()
    if not raw:
        raise RuntimeError("LIBRARY_DATA_URLS not configured")
    for url in [x.strip() for x in raw.split(",") if x.strip()]:
        payload = get_json_or_csv(url)
        rows = rows_from_payload(payload) if not isinstance(payload, list) else payload
        for row in rows:
            name = first(row, "library name", "library_name", "name")
            postcode = norm_postcode(first(row, "postcode", "post code")) or None
            if not name:
                continue
            record_id = first(row, "id", "library_id", "uprn") or f"{norm_name(str(name))}|{postcode or ''}"
            yield Candidate(
                source_name=source["name"], source_record_id=str(record_id),
                source_url=url, venue_name=str(name), postcode=postcode,
                address=first(row, "address", "address line 1", "address_line_1"),
                town_city=first(row, "town", "city", "local authority", "local_authority"),
                latitude=as_float(first(row, "latitude", "lat")),
                longitude=as_float(first(row, "longitude", "lng", "lon")),
                category="library", website=first(row, "url", "website"), payload=row,
            )


ADAPTERS = {"active_places": active_places_candidates, "library_open_data": library_candidates}


def venue_candidates(db, c: Candidate):
    fields = "id,venue_name,postcode,address,town_city,latitude,longitude,website,operator,category"
    if c.postcode:
        return db.table("venues").select(fields).ilike("postcode", c.postcode).limit(30).execute().data or []
    if c.latitude is not None and c.longitude is not None:
        # Supabase client has no portable radius primitive here; keep fallback
        # bounded and rely on name matching. Reference datasets should normally
        # include postcodes in the UK.
        return db.table("venues").select(fields).ilike("venue_name", f"%{c.venue_name[:40]}%").limit(20).execute().data or []
    return []


def choose_match(c: Candidate, existing: list[dict]):
    n = norm_name(c.venue_name)
    best = None
    for v in existing:
        vn = norm_name(v.get("venue_name"))
        score = difflib.SequenceMatcher(None, n, vn).ratio()
        exact_name = n == vn
        exact_pc = bool(c.postcode and norm_postcode(v.get("postcode")) == c.postcode)
        metres = distance_m(c.latitude, c.longitude, v.get("latitude"), v.get("longitude"))
        if exact_name and exact_pc:
            return v, "postcode_exact_name", 1.0
        if exact_pc and score >= 0.86:
            confidence = min(0.99, 0.78 + score * 0.20)
            if best is None or confidence > best[2]:
                best = (v, "postcode_fuzzy_name", confidence)
        elif metres is not None and metres <= 80 and score >= 0.75:
            confidence = min(0.97, 0.72 + score * 0.20)
            if best is None or confidence > best[2]:
                best = (v, "coordinates_name", confidence)
    return best


def upsert_provenance(db, venue_id: str, c: Candidate, method: str, confidence: float):
    row = {
        "venue_id": venue_id, "source_name": c.source_name,
        "source_record_id": c.source_record_id, "source_url": c.source_url,
        "source_role": "venue_reference", "match_method": method,
        "match_confidence": confidence, "source_payload": c.payload or {},
    }
    if not DRY_RUN:
        db.table("venue_sources").upsert(row, on_conflict="source_name,source_record_id").execute()


def enrich_existing(db, venue: dict, c: Candidate):
    patch = {}
    for field in ("website", "operator", "category"):
        if not venue.get(field) and getattr(c, field):
            patch[field] = getattr(c, field)
    if not venue.get("address") and c.address:
        patch["address"] = c.address
    if not venue.get("town_city") and c.town_city:
        patch["town_city"] = c.town_city
    if not venue.get("postcode") and c.postcode:
        patch["postcode"] = c.postcode
    if venue.get("latitude") is None and c.latitude is not None:
        patch["latitude"] = c.latitude
    if venue.get("longitude") is None and c.longitude is not None:
        patch["longitude"] = c.longitude
    if patch and not DRY_RUN:
        db.table("venues").update(patch).eq("id", venue["id"]).execute()


def create_hidden_venue(db, c: Candidate):
    synthetic = f"reference:{c.source_name}:{c.source_record_id}"
    row = {
        "venue_name": c.venue_name, "category": c.category,
        "address": c.address, "town_city": c.town_city, "postcode": c.postcode,
        "latitude": c.latitude, "longitude": c.longitude, "website": c.website,
        "operator": c.operator, "source": c.source_name, "source_url": synthetic,
        "discovered_source_url": c.source_url, "discovery_status": "discovered",
        "public_visible": False,
        "review_reason": f"New venue from {c.source_name}; review before publishing",
    }
    if DRY_RUN:
        return None
    data = db.table("venues").insert(row).execute().data or []
    return str(data[0]["id"]) if data else None


def flag_ambiguous(db, venue_id: str, c: Candidate):
    if DRY_RUN:
        return
    db.table("venues").update({
        "review_reason": f"Possible {c.source_name} match: {c.venue_name} ({c.postcode or 'no postcode'})"[:500]
    }).eq("id", venue_id).execute()


def main():
    db = db_client()
    sources = db.table("sources").select("id,name,url,source_role,source_adapter,active").eq("source_role", "venue_reference").eq("active", True).execute().data or []
    total = matched = created = ambiguous = 0
    for source in sources:
        adapter = ADAPTERS.get(source.get("source_adapter"))
        if not adapter:
            print(f"SKIP {source['name']}: no adapter")
            continue
        try:
            rows = adapter(source)
            for c in rows:
                total += 1
                if LIMIT and total > LIMIT:
                    break
                existing = venue_candidates(db, c)
                result = choose_match(c, existing)
                if result:
                    venue, method, confidence = result
                    if method == "postcode_fuzzy_name" and confidence < 0.95:
                        # Preserve the existing Dadspace policy: plausible same-postcode
                        # name mismatches go to review rather than auto-creating duplicates.
                        flag_ambiguous(db, str(venue["id"]), c)
                        ambiguous += 1
                        continue
                    enrich_existing(db, venue, c)
                    upsert_provenance(db, str(venue["id"]), c, method, confidence)
                    matched += 1
                else:
                    venue_id = create_hidden_venue(db, c)
                    if venue_id:
                        upsert_provenance(db, venue_id, c, "new_reference_venue", 1.0)
                    created += 1
            print(f"OK {source['name']}")
        except Exception as exc:
            print(f"FAILED {source['name']}: {type(exc).__name__}: {exc}")
    print(json.dumps({"dry_run": DRY_RUN, "seen": total, "matched": matched, "created_or_would_create": created, "ambiguous": ambiguous}))


if __name__ == "__main__":
    main()

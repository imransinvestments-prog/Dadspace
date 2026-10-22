#!/usr/bin/env python3
"""Council discovery: the top family spots per UK council from OpenStreetMap.

Responsibilities:
- take councils from geography_areas (latest geography release)
- fetch named family places inside each council's OSM boundary (ref:gss = ONS code)
- rank deterministically and keep the top 10, at most 3 per category
- keep only places not already in public.venues
- draft a dad-focused description and typical busy times from OSM tags only,
  stored as unverified review notes, never as venue facts
- write a strict JSON array per run and, when not a dry run, insert hidden
  discovered venues for the /ops review desk. Nothing is made public here.

Map data © OpenStreetMap contributors, ODbL.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import math
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

import requests

from venue_country import lookup_postcodes, normalize_postcode
from venue_reference_worker import Candidate, choose_match, distance_m, norm_name, norm_postcode

OVERPASS_URL = os.environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
POSTCODES_API = "https://api.postcodes.io/postcodes"
# overpass-api.de rejects browser-style agents with HTTP 406; identify the bot honestly.
UA = os.environ.get("USER_AGENT", "DadspaceVenueBot/2.0 (+https://www.dad-space.co.uk)")
SOURCE = "OpenStreetMap council discovery"
PROVENANCE = "osm-council-discovery"
TOP_N = 10
PER_CATEGORY = 3
NEAR_MISS_METRES = 150
NEAR_MISS_SCORE = 0.55
REFRESH_DAYS = int(os.environ.get("COUNCIL_DISCOVERY_REFRESH_DAYS", "180") or 180)
NO_BOUNDARY_RETRY_DAYS = 7

# Labels match the categories already stored for OSM venues, so the site's
# category artwork and filters treat new rows the same way.
CATEGORY_RULES = [
    ("tourism", "museum", "Museum", 5),
    ("tourism", "zoo", "Zoo / animal park", 5),
    ("tourism", "aquarium", "Aquarium", 5),
    ("tourism", "theme_park", "Theme park", 5),
    ("leisure", "water_park", "Water park", 4),
    ("leisure", "indoor_play", "Indoor / soft play centre", 4),
    ("leisure", "park", "Park", 4),
    ("leisure", "nature_reserve", "Nature reserve", 3),
    ("leisure", "playground", "Children’s playground", 2),
]
# Libraries are not discovered here (owner decision 23 Oct 2026, #243): the Public Library Open Data
# reference source already covers them and they rarely change.
FARM_LABEL, FARM_WEIGHT = "Farm", 5
# Owner decision 22 Oct 2026 (#243): Northern Ireland is left out for now (no ONS-coded OSM boundaries).
EXCLUDED_COUNCIL_PREFIXES = ("N",)
GENERIC_NAMES = {"playground", "play area", "childrens playground", "children s playground", "play park",
                 "park", "library", "museum", "nature reserve", "kids play area", "toddler play area"}

# A facility may only be mentioned when the spot has one of these tags (and not "=no").
FACILITY_TERMS = [
    (re.compile(r"baby[- ]?chang|changing (table|facilit)|nappy", re.I), {"changing_table"}),
    (re.compile(r"toilet|\bloos?\b|restroom", re.I), {"toilets"}),
    (re.compile(r"caf[eé]|coffee|snack", re.I), {"cafe"}),
    (re.compile(r"step[- ]free|wheelchair", re.I), {"wheelchair"}),
    (re.compile(r"\bparking\b|car park", re.I), {"parking"}),
    (re.compile(r"breast|baby[- ]feeding|feeding room", re.I), {"baby_feeding"}),
    # Age bands and prices are facts too; they need the matching tag.
    (re.compile(r"toddler|pre-?school|under[- ]?\d|\bages? \d|\d+\s?(months|years|yrs)\b", re.I),
     {"min_age", "max_age"}),
    (re.compile(r"\bfree\b|no charge|admission|ticket|\bprice", re.I), {"fee"}),
]
# Basic validation only (PRODUCT.md): drafts never vouch for safety or quality.
ENDORSEMENT = re.compile(r"\bsafe\b|safety|secure|vetted|verified|inspected|approved|guarantee|award|"
                         r"best in|number one|\bno\.? ?1\b", re.I)
EVIDENCE_KEYS = ("changing_table", "toilets", "wheelchair", "baby_feeding", "cafe", "parking", "opening_hours",
                 "fee", "website", "wikidata", "min_age", "max_age", "description")


def overpass_query(code: str) -> str:
    return f"""[out:json][timeout:180];
area["ref:gss"="{code}"]["boundary"="administrative"]->.a;
.a out ids;
(
  nwr["leisure"~"^(playground|park|nature_reserve|water_park|indoor_play)$"]["name"](area.a);
  nwr["tourism"~"^(museum|zoo|aquarium|theme_park)$"]["name"](area.a);
);
out tags center bb;"""


def fetch_overpass(code: str, retries: int = 3) -> dict:
    for attempt in range(retries + 1):
        try:
            r = requests.post(OVERPASS_URL, data={"data": overpass_query(code)}, timeout=240,
                              headers={"User-Agent": UA})
            if r.status_code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(min(60, 10 * 2 ** attempt))
                continue
            r.raise_for_status()
            return r.json()
        except (requests.Timeout, requests.ConnectionError):
            if attempt == retries:
                raise
            time.sleep(min(60, 10 * 2 ** attempt))
    raise RuntimeError("Overpass retries exhausted")


def classify(tags: dict) -> tuple[str, int] | None:
    if tags.get("tourism") == "zoo" and tags.get("zoo") == "petting_zoo":
        return FARM_LABEL, FARM_WEIGHT
    for key, value, label, weight in CATEGORY_RULES:
        if tags.get(key) == value:
            return label, weight
    return None


def bbox_area_km2(bounds: dict | None) -> float:
    if not bounds:
        return 0.0
    lat = (bounds["minlat"] + bounds["maxlat"]) / 2
    height = (bounds["maxlat"] - bounds["minlat"]) * 111.0
    width = (bounds["maxlon"] - bounds["minlon"]) * 111.0 * math.cos(math.radians(lat))
    return max(0.0, height * width)


def score(tags: dict, weight: int, bounds: dict | None, label: str) -> float:
    s = float(weight)
    s += 4 if tags.get("wikidata") else 0
    s += 1 if tags.get("wikipedia") else 0
    s += 1 if tags.get("website") or tags.get("contact:website") else 0
    s += 1 if tags.get("opening_hours") else 0
    s += 2 if tags.get("changing_table") == "yes" else 0
    s += 1 if tags.get("toilets") == "yes" else 0
    s += 1 if tags.get("wheelchair") == "yes" else 0
    s += 1 if tags.get("baby_feeding") in ("yes", "room") else 0
    if label in ("Park", "Nature reserve"):
        s += min(3.0, math.log1p(bbox_area_km2(bounds) * 10))
    return round(s, 3)


def spots_from_overpass(data: dict) -> tuple[bool, list[dict]]:
    """Return (boundary_found, candidate spots) from an Overpass response."""
    boundary = any(e.get("type") == "area" for e in data.get("elements", []))
    spots = []
    for e in data.get("elements", []):
        if e.get("type") not in ("node", "way", "relation"):
            continue
        tags = e.get("tags") or {}
        name = (tags.get("name") or "").strip()
        if not name or norm_name(name) in GENERIC_NAMES:
            continue
        if tags.get("access") in ("private", "no") or tags.get("disused") == "yes":
            continue
        kind = classify(tags)
        if not kind:
            continue
        label, weight = kind
        lat = e.get("lat", (e.get("center") or {}).get("lat"))
        lon = e.get("lon", (e.get("center") or {}).get("lon"))
        bounds = e.get("bounds")
        if (lat is None or lon is None) and bounds:
            # Overpass returns bounds instead of a centre for ways and relations when both are asked for.
            lat = round((bounds["minlat"] + bounds["maxlat"]) / 2, 7)
            lon = round((bounds["minlon"] + bounds["maxlon"]) / 2, 7)
        if lat is None or lon is None:
            continue
        spots.append({
            "osm_type": e["type"], "osm_id": e["id"], "name": name, "category": label,
            "lat": lat, "lng": lon, "tags": tags, "bounds": bounds,
            "score": score(tags, weight, e.get("bounds"), label),
        })
    return boundary, spots


def ordered(spots: list[dict]) -> list[dict]:
    """Highest score first; OSM type and id break ties so reruns agree."""
    return sorted(spots, key=lambda s: (-s["score"], s["osm_type"], s["osm_id"]))


def rank(spots: list[dict], limit: int = TOP_N, per_category: int = PER_CATEGORY) -> list[dict]:
    kept, counts = [], {}
    for s in ordered(spots):
        if counts.get(s["category"], 0) >= per_category:
            continue
        counts[s["category"]] = counts.get(s["category"], 0) + 1
        kept.append(s)
        if len(kept) == limit:
            break
    for i, s in enumerate(kept, 1):
        s["rank"] = i
    return kept


def osm_url(spot: dict) -> str:
    return f"https://www.openstreetmap.org/{spot['osm_type']}/{spot['osm_id']}"


def spot_key(spot: dict) -> str:
    return f"{spot['osm_type']}/{spot['osm_id']}"


class VenueIndex:
    """Existing venues indexed by OSM element, postcode and a ~1 km grid."""

    def __init__(self, rows: list[dict]):
        self.by_osm, self.by_pc, self.by_cell = {}, {}, {}
        for row in rows:
            self.add(row)

    @staticmethod
    def cell(lat, lng):
        return (round(float(lat), 2), round(float(lng), 2))

    def add(self, row: dict):
        for url in (row.get("source_url"), row.get("discovered_source_url")):
            m = re.search(r"openstreetmap\.org/(node|way|relation)/(\d+)", url or "")
            if m:
                self.by_osm[f"{m.group(1)}/{m.group(2)}"] = row
        if row.get("postcode"):
            self.by_pc.setdefault(norm_postcode(row["postcode"]), []).append(row)
        if row.get("latitude") is not None and row.get("longitude") is not None:
            self.by_cell.setdefault(self.cell(row["latitude"], row["longitude"]), []).append(row)

    def nearby(self, lat, lng, postcode=None) -> list[dict]:
        found = {}
        la, lo = self.cell(lat, lng)
        for dla in (-0.01, 0, 0.01):
            for dlo in (-0.01, 0, 0.01):
                for row in self.by_cell.get((round(la + dla, 2), round(lo + dlo, 2)), []):
                    found[id(row)] = row
        for row in self.by_pc.get(norm_postcode(postcode), []) if postcode else []:
            found[id(row)] = row
        return list(found.values())


def match_existing(spot: dict, index: VenueIndex):
    """Return ("existing", venue), ("possible", venue) or (None, None)."""
    if spot_key(spot) in index.by_osm:
        return "existing", index.by_osm[spot_key(spot)]
    # The resolved postcode (once known) also feeds choose_match's postcode rules.
    postcode = norm_postcode(spot.get("postcode") or spot["tags"].get("addr:postcode")) or None
    nearby = index.nearby(spot["lat"], spot["lng"], postcode)
    c = Candidate(source_name=SOURCE, source_record_id=spot_key(spot), source_url=osm_url(spot),
                  venue_name=spot["name"], postcode=postcode, latitude=spot["lat"], longitude=spot["lng"])
    hit = choose_match(c, nearby)
    if hit:
        return "existing", hit[0]
    n, best = norm_name(spot["name"]), None
    for v in nearby:
        ratio = difflib.SequenceMatcher(None, n, norm_name(v.get("venue_name"))).ratio()
        # A park or building outline can be far wider than 80 m: a similar name inside it is the same place.
        if inside(spot.get("bounds"), v) and ratio >= 0.75:
            return "existing", v
        metres = distance_m(spot["lat"], spot["lng"], v.get("latitude"), v.get("longitude"))
        near = (metres is not None and metres <= NEAR_MISS_METRES) or inside(spot.get("bounds"), v)
        if near and ratio >= NEAR_MISS_SCORE and (best is None or ratio > best[0]):
            best = (ratio, v)
    return ("possible", best[1]) if best else (None, None)


def inside(bounds: dict | None, venue: dict) -> bool:
    if not bounds or venue.get("latitude") is None or venue.get("longitude") is None:
        return False
    return (bounds["minlat"] <= float(venue["latitude"]) <= bounds["maxlat"]
            and bounds["minlon"] <= float(venue["longitude"]) <= bounds["maxlon"])


def reverse_postcodes(points: list[tuple[float, float]]) -> list[dict | None]:
    """Nearest postcode for each (lat, lng); failures stay None."""
    out: list[dict | None] = []
    for offset in range(0, len(points), 100):
        batch = points[offset:offset + 100]
        body = {"geolocations": [{"latitude": la, "longitude": lo, "radius": 1000, "limit": 1} for la, lo in batch]}
        try:
            req = urllib.request.Request(POSTCODES_API, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.load(response)
            entries = data.get("result") or []
            if len(entries) != len(batch):
                raise ValueError("Incomplete reverse geocode response")
            out.extend(((e.get("result") or [None])[0]) for e in entries)
        except (OSError, ValueError, KeyError, TypeError):
            out.extend([None] * len(batch))
    return out


def resolve_postcodes(spots: list[dict], council_code: str) -> list[dict]:
    """Attach postcodes and record where each came from.

    Council membership is already exact from the OSM boundary, so a postcode in another council
    (edge-of-borough nearest postcode, or a wrong addr:postcode) is flagged for review, not dropped.
    """
    for s in spots:
        tagged = norm_postcode(s["tags"].get("addr:postcode")) or None
        s["postcode"], s["postcode_source"] = tagged, "osm_tag" if tagged else None
    if council_code.startswith("N"):
        # Northern Ireland postcode geography is not licensed for this use; keep OSM addresses only.
        for s in spots:
            s["council_check"] = "not_applicable_ni"
        return spots
    tagged = [s for s in spots if s["postcode_source"]]
    untagged = [s for s in spots if not s["postcode_source"]]
    forward = lookup_postcodes(s["postcode"] for s in tagged)
    found = {id(s): forward.get(normalize_postcode(s["postcode"])) for s in tagged}
    found.update({id(s): r for s, r in zip(untagged, reverse_postcodes([(s["lat"], s["lng"]) for s in untagged]))})
    for s in spots:
        result = found.get(id(s))
        if not result or result.get("_error"):
            s["council_check"] = "unavailable"
            continue
        district = (result.get("codes") or {}).get("admin_district")
        if not s["postcode_source"]:
            s["postcode"], s["postcode_source"] = result.get("postcode"), "reverse_nearest"
        if district and district != council_code:
            s["council_check"] = "postcode_other_council"
            continue
        s["town"] = result.get("admin_district")
        s["council_check"] = "postcode_in_council"
    return spots


def stored_postcode(spot: dict) -> str | None:
    """Only a postcode OSM states is a venue fact; a nearest-postcode guess stays a review hint."""
    return spot.get("postcode") if spot.get("postcode_source") == "osm_tag" else None


def address_for(spot: dict, council_name: str) -> str:
    t = spot["tags"]
    street = " ".join(x for x in (t.get("addr:housenumber"), t.get("addr:street")) if x)
    seen, out = set(), []
    for part in (street, t.get("addr:city") or t.get("addr:town") or spot.get("town") or council_name,
                 stored_postcode(spot)):
        if part and part.lower() not in seen:
            seen.add(part.lower())
            out.append(part)
    return ", ".join(out)


def evidence_tags(spot: dict) -> list[str]:
    return [f"{k}={spot['tags'][k]}" for k in EVIDENCE_KEYS if spot["tags"].get(k)]


NOTES_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "description": {"type": "string"},
            "peak_busy_times": {"type": "string"},
            "evidence_tags": {"type": "array", "items": {"type": "string"}},
        },
    },
}


def notes_prompt(council_name: str, spots: list[dict]) -> str:
    facts = [{"key": spot_key(s), "name": s["name"], "category": s["category"], "tags": evidence_tags(s)}
             for s in spots]
    return (
        "You write short notes for Dadspace, a UK site helping parents and carers find family days out.\n"
        f"Council: {council_name}. For each place below write:\n"
        "- description: exactly 2 sentences on why it is a good weekend spot for a dad with young kids.\n"
        "  Use only the facts given. Mention a facility (baby changing, toilets, cafe, step-free access, parking,\n"
        "  feeding room) ONLY if a matching tag is listed with a value other than 'no'. Never invent prices,\n"
        "  awards, events, opening times or history. Do not state ages (toddlers, under-5s) or that it is free\n"
        "  unless a min_age/max_age or fee tag says so, and never call a place safe, vetted or the best.\n"
        "- peak_busy_times: one short phrase for the typical busy pattern of this kind of place,\n"
        "  e.g. 'Weekend late mornings and school holidays'. It is a general pattern, not measured data.\n"
        "- evidence_tags: the listed tags you relied on, copied exactly, or an empty list.\n"
        "Return one item per place, using its key. British English.\n\n"
        + json.dumps(facts, ensure_ascii=False)
    )


def check_note(spot: dict, note: dict) -> dict:
    tags = set(evidence_tags(spot))
    present = {k for k in EVIDENCE_KEYS if spot["tags"].get(k) and spot["tags"][k] != "no"}
    description = (note.get("description") or "").strip() or None
    rejected = None
    if description and ENDORSEMENT.search(description):
        description, rejected = None, "endorsement_claim"
    if description:
        for pattern, required in FACILITY_TERMS:
            if pattern.search(description) and not required & present:
                description, rejected = None, "unsupported_facility_claim"
                break
    return {"description": description, "peak_busy_times": (note.get("peak_busy_times") or "").strip() or None,
            "evidence_tags": [t for t in note.get("evidence_tags") or [] if t in tags], "note_rejected": rejected}


def draft_notes(generator, council_name: str, spots: list[dict]) -> dict:
    """Map spot key -> checked notes. Spots missing from the reply keep empty notes."""
    if generator is None or not spots:
        return {}
    items = generator.generate(notes_prompt(council_name, spots), NOTES_SCHEMA)
    by_key = {spot_key(s): s for s in spots}
    return {i["key"]: check_note(by_key[i["key"]], i) for i in items if i.get("key") in by_key}


OUTPUT_FIELDS = ["name", "category", "address", "description", "peak_busy_times", "council_code",
                 "council_name", "postcode", "postcode_source", "lat", "lng", "osm_type", "osm_id", "source_url",
                 "claims_status", "evidence_tags", "rank", "possible_duplicate_of", "council_check",
                 "note_rejected"]


def output_record(spot: dict, council: dict, notes: dict, possible) -> dict:
    note = notes.get(spot_key(spot)) or {}
    record = {
        "name": spot["name"], "category": spot["category"], "address": address_for(spot, council["name"]),
        "description": note.get("description"), "peak_busy_times": note.get("peak_busy_times"),
        "council_code": council["code"], "council_name": council["name"], "postcode": spot.get("postcode"),
        "postcode_source": spot.get("postcode_source"), "lat": spot["lat"], "lng": spot["lng"], "osm_type": spot["osm_type"], "osm_id": spot["osm_id"],
        "source_url": osm_url(spot), "claims_status": "unverified",
        "evidence_tags": note.get("evidence_tags") or [], "rank": spot["rank"],
        "possible_duplicate_of": ({"venue_id": possible.get("id"), "venue_name": possible.get("venue_name")}
                                  if possible else None),
        "council_check": spot.get("council_check"), "note_rejected": note.get("note_rejected"),
    }
    validate_record(record)
    return record


def validate_record(record: dict):
    if list(record) != OUTPUT_FIELDS:
        raise ValueError("output record fields out of order")
    for key in ("name", "category", "address", "council_code", "council_name", "osm_type", "source_url"):
        if not isinstance(record[key], str) or not record[key]:
            raise ValueError(f"output record missing {key}")
    if record["claims_status"] != "unverified":
        raise ValueError("generated notes must stay unverified")
    for key in ("description", "peak_busy_times", "postcode"):
        if record[key] is not None and not isinstance(record[key], str):
            raise ValueError(f"output record {key} must be text or null")
    if not isinstance(record["lat"], (int, float)) or not isinstance(record["lng"], (int, float)):
        raise ValueError("output record needs coordinates")


def review_reason(record: dict) -> str:
    parts = [f"Council discovery {record['council_code']}: new OSM candidate; AI description and busy times unverified"]
    if record["postcode_source"] == "reverse_nearest":
        parts.append(f"nearest postcode {record['postcode']} inferred, not stored")
    if record["council_check"] == "postcode_other_council":
        parts.append("postcode lies in a neighbouring council")
    if record["possible_duplicate_of"]:
        dup = record["possible_duplicate_of"]
        parts.append(f"possible duplicate of {dup['venue_name']} ({dup['venue_id']})")
    return "; ".join(parts)[:500]


def venue_row(record: dict) -> dict:
    """Hidden discovered venue. This path never publishes."""
    return {
        "venue_name": record["name"], "category": record["category"], "address": record["address"],
        "town_city": record["council_name"],
        "postcode": record["postcode"] if record["postcode_source"] == "osm_tag" else None,
        "latitude": record["lat"], "longitude": record["lng"], "source": SOURCE,
        "source_url": record["source_url"], "discovered_source_url": record["source_url"],
        "licence": "ODbL", "discovery_status": "discovered", "public_visible": False,
        "review_reason": review_reason(record),
    }


def provenance_row(venue_id: str, record: dict, spot: dict) -> dict:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    return {
        "venue_id": str(venue_id), "source_name": PROVENANCE, "source_record_id": spot_key(spot),
        "source_url": record["source_url"], "source_role": "venue_reference", "match_method": "new",
        "match_confidence": 1.0,
        "source_payload": {"osm_tags": spot["tags"], "council_code": record["council_code"],
                           "rank": record["rank"], "score": spot["score"], "postcode": record["postcode"],
                           "postcode_source": record["postcode_source"],
                           "council_check": record["council_check"],
                           "possible_duplicate_of": record["possible_duplicate_of"],
                           "draft": {"description": record["description"],
                                     "peak_busy_times": record["peak_busy_times"],
                                     "evidence_tags": record["evidence_tags"], "claims_status": "unverified"},
                           "attribution": "© OpenStreetMap contributors, ODbL"},
        "last_seen_at": now, "updated_at": now,
    }


def load_venue_rows(db) -> list[dict]:
    rows, start = [], 0
    while True:
        # Paging needs a fixed order: unordered pages can overlap or skip rows, and a skipped
        # row lets an existing venue (e.g. Hanwell Zoo, 22 Oct dry run) through as "new".
        part = (db.table("venues").select("id,venue_name,postcode,latitude,longitude,source_url,discovered_source_url")
                .order("id").range(start, start + 999).execute().data or [])
        rows.extend(part)
        if len(part) < 1000:
            return rows
        start += 1000


def load_councils(db) -> tuple[str, list[dict]]:
    release = (db.table("geography_releases").select("id").order("imported_at", desc=True)
               .limit(1).execute().data or [])
    if not release:
        raise RuntimeError("No geography release is loaded")
    rid = release[0]["id"]
    councils = (db.table("geography_areas").select("code,name").eq("release_id", rid)
                .eq("kind", "council").order("code").execute().data or [])
    return rid, councils


def due_councils(db, councils: list[dict], count: int) -> list[dict]:
    runs = db.table("venue_council_discovery_runs").select("council_code,ran_at,status").execute().data or []
    now = dt.datetime.now(dt.timezone.utc)

    def fresh(r):
        ran = dt.datetime.fromisoformat(r["ran_at"].replace("Z", "+00:00"))
        if r.get("status") == "ok":
            return ran > now - dt.timedelta(days=REFRESH_DAYS)
        if r.get("status") == "no_boundary":
            # Northern Ireland boundaries carry no ONS code in OSM (known gap); elsewhere a missing
            # boundary is usually an OSM edit, so try again after a week.
            days = REFRESH_DAYS if r["council_code"].startswith("N") else NO_BOUNDARY_RETRY_DAYS
            return ran > now - dt.timedelta(days=days)
        return False

    recent = {r["council_code"] for r in runs if fresh(r)}
    return [c for c in councils if c["code"] not in recent][:count]


def make_generator(enabled: bool):
    if not enabled:
        return None
    from llm_provider import FatalLLMError, StructuredGenerator
    try:
        return StructuredGenerator("VENUE_DISCOVERY", "gemini-3.6-flash", timeout=90, output_limit=4000,
                                   temperature=0.2)
    except FatalLLMError as exc:
        print(f"LLM unavailable, notes left empty: {exc}", file=sys.stderr)
        return None


def select_new(spots: list[dict], index: VenueIndex) -> tuple[list[dict], dict, dict]:
    """Walk the ranked pool, skipping known venues, until the category-capped top list has slack."""
    picked, possible_for, counts = [], {}, {}
    stats = {"existing": 0, "possible": 0}
    for spot in ordered(spots):
        if len(picked) >= TOP_N * 2:  # slack for spots postcode checks place in a neighbouring council
            break
        if counts.get(spot["category"], 0) >= PER_CATEGORY * 2:
            continue
        outcome, venue = match_existing(spot, index)
        if outcome == "existing":
            stats["existing"] += 1
            continue
        if outcome == "possible":
            possible_for[spot_key(spot)] = venue
            stats["possible"] += 1
        counts[spot["category"]] = counts.get(spot["category"], 0) + 1
        picked.append(spot)
    return picked, possible_for, stats


def stored_osm_urls(db, urls: list[str]) -> set[str]:
    """Direct lookup of OSM URLs already in venues, independent of the bulk-loaded index."""
    if not urls:
        return set()
    found = set()
    for column in ("source_url", "discovered_source_url"):
        rows = db.table("venues").select(column).in_(column, urls).execute().data or []
        found.update(r[column] for r in rows if r.get(column))
    return found


def discover_council(council: dict, index: VenueIndex, generator, fetch=None,
                     resolve=None, known=None) -> tuple[dict, list[tuple[dict, dict]]]:
    fetch, resolve = fetch or fetch_overpass, resolve or resolve_postcodes  # looked up per call
    stats = {"code": council["code"], "name": council["name"], "status": "ok", "candidates": 0, "new": 0,
             "existing": 0, "possible": 0}
    boundary, spots = spots_from_overpass(fetch(council["code"]))
    if not boundary:
        stats["status"] = "no_boundary"
        return stats, []
    stats["candidates"] = len(spots)
    picked, possible_for, counts = select_new(spots, index)
    stats.update(counts)
    if known is not None:
        # Second, direct check by OSM URL so an existing place can never be offered as new.
        stored = known([osm_url(s) for s in picked])
        stats["existing"] += sum(osm_url(s) in stored for s in picked)
        picked = [s for s in picked if osm_url(s) not in stored]
    resolved = []
    for spot in resolve(picked, council["code"]):
        # Overpass area filters return outlines that only cross into the council (a park over the
        # borough line). If its postcode is in the neighbour, the neighbour's own run returns it too.
        # Points are genuinely inside the boundary, so they stay, flagged for the reviewer.
        if spot.get("council_check") == "postcode_other_council" and spot["osm_type"] != "node":
            stats["other_council"] = stats.get("other_council", 0) + 1
            continue
        # Second pass now the postcode is known: choose_match's postcode rules can only fire here.
        outcome, venue = match_existing(spot, index)
        if outcome == "existing":
            stats["existing"] += 1
            possible_for.pop(spot_key(spot), None)
            continue
        if outcome == "possible" and spot_key(spot) not in possible_for:
            possible_for[spot_key(spot)] = venue
            stats["possible"] += 1
        resolved.append(spot)
    top = rank(resolved)
    notes = {}
    if generator is not None and top:
        try:
            notes = draft_notes(generator, council["name"], top)
        except Exception as exc:  # noqa: BLE001 - notes are optional; the places are still useful
            stats["notes_error"] = type(exc).__name__
            if type(exc).__name__ in ("BudgetExhausted", "FatalLLMError"):
                raise
    records = []
    for spot in top:
        record = output_record(spot, council, notes, possible_for.get(spot_key(spot)))
        records.append((record, spot))
        index.add({"id": None, "venue_name": spot["name"], "postcode": spot.get("postcode"),
                   "latitude": spot["lat"], "longitude": spot["lng"], "source_url": record["source_url"]})
    stats["new"] = len(records)
    return stats, records


def run(db, *, dry_run: bool, councils_per_run: int = 10, council: str | None = None, llm: bool = True,
        max_llm_calls: int = 0, venue_rows: list[dict] | None = None, councils: list[dict] | None = None,
        release_id: str | None = None, out_dir: str = "review/council-discovery") -> dict:
    if councils is None:
        release_id, councils = load_councils(db)
    councils = [c for c in councils if not c["code"].startswith(EXCLUDED_COUNCIL_PREFIXES)]
    if council:
        selected = [c for c in councils if c["code"] == council]
    elif db is not None:
        selected = due_councils(db, councils, councils_per_run)
    else:
        selected = councils[:councils_per_run]
    index = VenueIndex(venue_rows if venue_rows is not None else load_venue_rows(db))
    generator, llm_calls = make_generator(llm), 0
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    records, summary = [], {"dry_run": dry_run, "run_id": run_id, "councils": []}
    pause = float(os.environ.get("OVERPASS_PAUSE_SECONDS", "5") or 0)
    known = (lambda urls: stored_osm_urls(db, urls)) if db is not None else None
    for i, c in enumerate(selected):
        if i:
            time.sleep(pause)
        use = generator if not max_llm_calls or llm_calls < max_llm_calls else None
        try:
            try:
                stats, found = discover_council(c, index, use, known=known)
            except Exception as exc:
                # FatalLLMError subclasses RuntimeError, so the LLM stop is checked first:
                # stop drafting notes for the rest of the run but keep this council's places.
                if type(exc).__name__ not in ("BudgetExhausted", "FatalLLMError"):
                    raise
                print(f"LLM stopped at {c['code']}: {type(exc).__name__}", file=sys.stderr)
                generator = use = None
                stats, found = discover_council(c, index, None, known=known)
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            stats, found = {"code": c["code"], "name": c["name"], "status": "failed",
                            "error": type(exc).__name__}, []
        llm_calls += 1 if use is not None and found else 0
        records.extend(found)
        summary["councils"].append(stats)
    summary["artifact"] = write_artifact([r for r, _ in records], out_dir, run_id)
    if not dry_run and db is not None:
        summary["inserted"] = insert_records(db, records)
        for stats in summary["councils"]:
            record_run(db, stats, release_id, summary["artifact"])
    summary["llm_calls"] = llm_calls
    return summary


def record_run(db, stats: dict, release_id: str | None, artifact: str):
    db.table("venue_council_discovery_runs").insert({
        "council_code": stats["code"], "release_id": release_id, "status": stats["status"],
        "candidates": stats.get("candidates", 0), "new_count": stats.get("new", 0), "artifact_path": artifact,
    }).execute()


def write_artifact(records: list[dict], out_dir: str, run_id: str) -> str:
    path = Path(out_dir) / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path.as_posix()


def insert_records(db, records: list[tuple[dict, dict]]) -> int:
    """Insert hidden venues. Possible duplicates go in too, named in the review reason, so a
    reviewer can merge or approve them rather than the place being lost with the artifact."""
    inserted = 0
    for offset in range(0, len(records), 100):
        batch = records[offset:offset + 100]
        rows = [venue_row(r) for r, _ in batch]
        if any(row["public_visible"] is not False for row in rows):
            raise RuntimeError("council discovery must not publish venues")
        saved = db.table("venues").upsert(rows, on_conflict="source_url", ignore_duplicates=True).execute().data or []
        ids = {x["source_url"]: x["id"] for x in saved if x.get("source_url") and x.get("id")}
        provs = [provenance_row(ids[r["source_url"]], r, s) for r, s in batch if r["source_url"] in ids]
        if provs:
            db.table("venue_sources").upsert(provs, on_conflict="source_name,source_record_id").execute()
        inserted += len(ids)
    return inserted


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--councils-per-run", type=int, default=int(os.environ.get("COUNCILS_PER_RUN", "10") or 10))
    p.add_argument("--council", help="One ONS council code, e.g. E09000009")
    p.add_argument("--dry-run", action="store_true", default=os.environ.get("DRY_RUN", "true").lower() == "true")
    p.add_argument("--write", dest="dry_run", action="store_false", help="Insert hidden venues")
    p.add_argument("--no-llm", dest="llm", action="store_false",
                   default=os.environ.get("COUNCIL_DISCOVERY_LLM", "true").lower() == "true")
    p.add_argument("--max-llm-calls", type=int,
                   default=int(os.environ.get("COUNCIL_DISCOVERY_MAX_LLM_CALLS", "0") or 0))
    p.add_argument("--venues-json", help="Offline dry run: existing venues to check against")
    p.add_argument("--councils-json", help="Offline dry run: [{code, name}] instead of geography_areas")
    p.add_argument("--out-dir", default="review/council-discovery")
    a = p.parse_args(argv)
    offline = bool(a.venues_json or a.councils_json)
    if offline and not (a.venues_json and a.councils_json and a.dry_run):
        p.error("offline runs need --venues-json, --councils-json and a dry run")
    db = None
    if not offline:
        from supabase import create_client
        db = create_client(os.environ["SUPABASE_URL"],
                           os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"])
    load = lambda path: json.loads(Path(path).read_text(encoding="utf-8")) if path else None  # noqa: E731
    summary = run(db, dry_run=a.dry_run, councils_per_run=a.councils_per_run, council=a.council, llm=a.llm,
                  max_llm_calls=a.max_llm_calls, venue_rows=load(a.venues_json),
                  councils=load(a.councils_json), out_dir=a.out_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

"""Name unnamed public playgrounds from their nearest road (owner rule, 22 October 2026).

Most unnamed playgrounds already show "<street> Playground", derived from their address.
The 386 in artefacts/data/unnamed-playgrounds-2026-10-22.csv have no street on record and
showed "Unnamed children's playground (way/...)". For each, this asks OpenStreetMap
Nominatim for the nearest named road (one request per second, as its usage policy
requires) and writes:
  artefacts/data/unnamed-playground-labels-2026-10-22.json  evidence for every playground
  supabase/unnamed-playground-labels-2026-10-22.sql         transaction for the owner to run
Where no road is found the SQL uses "Playground near <nearby settlement>". The source
name stays blank, so a real name from OpenStreetMap always takes over.

  python scripts/label-unnamed-playgrounds.py
"""
import csv
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "artefacts/data/unnamed-playgrounds-2026-10-22.csv"
EVIDENCE = ROOT / "artefacts/data/unnamed-playground-labels-2026-10-22.json"
SQL = ROOT / "supabase/unnamed-playground-labels-2026-10-22.sql"
USER_AGENT = "Dadspace/1.0 (+https://github.com/imransinvestments-prog/Dadspace)"
# Nominatim address parts that name a street people would recognise.
ROAD_KEYS = ("road", "pedestrian", "residential")
# A bare classification number ("A38", "B1234") is not a name anyone would call a playground by.
ROAD_NUMBER = re.compile(r"[ABM]\d+[A-Z]?(\s*\(M\))?", re.I)


# Public streets only. Service roads, footways, paths, tracks, cycleways and bridleways are often
# named after a site or route ("Lower Lacon Caravan Park", "Segway Track", "Hicks Lodge Trail"),
# which would read as a fake street; those playgrounds fall back to "Playground near <town>".
STREET_TYPES = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential",
                "living_street", "pedestrian", "road"}


def street_kind(kind):
    category, _, kind_type = (kind or "").partition("/")
    return category == "highway" and kind_type in STREET_TYPES


def road_from(result):
    if not street_kind(f"{(result or {}).get('category')}/{(result or {}).get('type')}"):
        return None
    address = (result or {}).get("address") or {}
    for key in ROAD_KEYS:
        value = re.sub(r"\s+", " ", str(address.get(key) or "")).strip()
        if value and not ROAD_NUMBER.fullmatch(value):
            return value
    return None


def distance_m(lat1, lon1, lat2, lon2):
    rad = math.pi / 180
    h = (math.sin((lat2 - lat1) * rad / 2) ** 2
         + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin((lon2 - lon1) * rad / 2) ** 2)
    return round(2 * 6371000 * math.asin(math.sqrt(h)))


def reverse(lat, lon):
    query = urllib.parse.urlencode({"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 17, "addressdetails": 1})
    request = urllib.request.Request(f"https://nominatim.openstreetmap.org/reverse?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def sql_text(value):
    return "null" if value is None else "'" + value.replace("'", "''") + "'"


def build_sql(rows):
    values = ",\n  ".join(f"('{r['id']}'::uuid, {sql_text(r['road'])})" for r in rows)
    return f"""-- Owner rule, 22 October 2026: unnamed playgrounds are labelled "<road> Playground".
-- These {len(rows)} had no street on record; roads come from OpenStreetMap Nominatim reverse
-- geocoding (evidence: artefacts/data/unnamed-playground-labels-2026-10-22.json). Where none
-- was found the label is "Playground near <nearby settlement>". Only the display label and a
-- note change; the source name stays blank. Rows already renamed or named are left alone.
begin;
with labels(id, road) as (values
  {values}
)
update public.venues v
set venue_label = case when l.road is not null then l.road || ' Playground' else 'Playground near ' || v.nearby_settlement end,
    notes = concat_ws(' ', v.notes, case when l.road is not null
      then 'Display label derived 2026-10-22 from the nearest named road in OpenStreetMap; not an official name.'
      else 'Display label derived 2026-10-22 from the nearby settlement; not an official name.' end)
from labels l
where v.id = l.id
  and coalesce(trim(v.venue_name), '') = ''
  and v.venue_label like 'Unnamed%'
  and (l.road is not null or v.nearby_settlement is not null);

-- Expect zero: no public unnamed playground still shows an OpenStreetMap id.
select count(*) as still_unnamed from public.venues
where category = 'Children’s playground' and public_visible
  and coalesce(trim(venue_name), '') = '' and venue_label like 'Unnamed%';
commit;

-- Rollback: restore the previous "Unnamed children’s playground (way/…)" label from the source
-- URL and remove the note, for rows this file changed and that are still unnamed.
-- update public.venues set
--   venue_label = 'Unnamed children’s playground (' || substring(source_url from 'openstreetmap\\.org/(.+)$') || ')',
--   notes = nullif(trim(replace(replace(notes,
--     ' Display label derived 2026-10-22 from the nearest named road in OpenStreetMap; not an official name.', ''),
--     ' Display label derived 2026-10-22 from the nearby settlement; not an official name.', '')), '')
-- where notes like '%Display label derived 2026-10-22%' and coalesce(trim(venue_name), '') = '';
"""


def rebuild():
    """Reapply the street rule to saved evidence without querying Nominatim again."""
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    for entry in data["playgrounds"]:
        entry["address_road"] = entry.get("address_road", entry["road"])
        entry["road"] = entry["address_road"] if street_kind(entry.get("matched_kind")) else None
    EVIDENCE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    SQL.write_text(build_sql(data["playgrounds"]), encoding="utf-8")
    print(f"Rebuilt: {sum(r['road'] is not None for r in data['playgrounds'])} street names")
    return 0


def main():
    if "--rebuild" in sys.argv:
        return rebuild()
    rows = list(csv.DictReader(INPUT.open(encoding="utf-8")))
    results = []
    for i, row in enumerate(rows, 1):
        lat, lon = float(row["latitude"]), float(row["longitude"])
        entry = {"id": row["id"], "latitude": lat, "longitude": lon, "road": None}
        try:
            result = reverse(lat, lon)
            entry.update(road=road_from(result), osm=f"{result.get('osm_type')}/{result.get('osm_id')}",
                         matched_kind=f"{result.get('category')}/{result.get('type')}",
                         matched=result.get("display_name"),
                         distance_m=distance_m(lat, lon, float(result["lat"]), float(result["lon"])) if result.get("lat") else None)
        except Exception as exc:  # A failed lookup falls back to the settlement; it is recorded, not hidden.
            entry["error"] = f"{type(exc).__name__}: {exc}"[:200]
        results.append(entry)
        if i % 50 == 0:
            print(f"{i}/{len(rows)} looked up, {sum(r['road'] is not None for r in results)} roads found", flush=True)
        time.sleep(1.1)
    EVIDENCE.write_text(json.dumps({"generated": time.strftime("%Y-%m-%d"), "source": "OpenStreetMap Nominatim reverse geocoding, zoom 17",
                                    "playgrounds": results}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    SQL.write_text(build_sql(results), encoding="utf-8")
    found = sum(r["road"] is not None for r in results)
    print(f"Done: {found} road names, {len(results) - found} settlement fallbacks, {sum('error' in r for r in results)} lookup errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Refresh a bounded, attributed development reference; never writes a database.

Official administrative codes are reused from the app's pinned ONS lookup.
Only GB postcode samples are requested; NI geocodes are withheld for licence review.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SAMPLES = [
    ('W3 9LN', 'Acton pilot', 'pilot'), ('SW1A 1AA', 'Central London', 'urban'),
    ('M2 5DB', 'Manchester', 'urban'), ('NE1 4LP', 'Newcastle', 'urban'),
    ('DH1 3LE', 'Durham', 'town'), ('LS1 3AD', 'Leeds', 'urban'),
    ('S1 2HH', 'Sheffield', 'urban'), ('NG1 2LH', 'Nottingham', 'urban'),
    ('LE1 5DB', 'Leicester', 'urban'), ('B1 1BB', 'Birmingham', 'urban'),
    ('CV1 5RR', 'Coventry', 'urban'), ('CB2 1TN', 'Cambridge', 'town'),
    ('NR2 1NH', 'Norwich', 'town'), ('OX1 2JD', 'Oxford', 'town'),
    ('BN1 1EE', 'Brighton', 'coastal'), ('BS1 5TR', 'Bristol', 'urban'),
    ('PL1 2AA', 'Plymouth', 'coastal'), ('TR1 2NE', 'Truro', 'town'),
    ('LA22 9BU', 'Ambleside', 'rural_destination'), ('SY8 1AS', 'Ludlow', 'rural_destination'),
    ('PO30 1TY', 'Isle of Wight', 'island'), ('KW15 1NY', 'Orkney', 'island'),
    ('HS1 2BW', 'Western Isles', 'island'), ('EH1 1YZ', 'Edinburgh', 'urban'),
    ('G1 2FF', 'Glasgow', 'urban'), ('CF10 1EP', 'Cardiff', 'urban'),
    ('LL57 2DG', 'Bangor', 'town'), ('CH4 8SG', 'England/Wales border vicinity', 'boundary_vicinity'),
    ('BT1 5GS', 'Belfast', 'licence_blocked'), ('BT48 7NN', 'Derry', 'licence_blocked'),
]


def main():
    pinned = json.loads((ROOT/'news_geography.json').read_text())['reference']
    endpoint = pinned['source']+'/query'
    response = requests.get(endpoint, params=dict(where='1=1',
        outFields='LAD26CD,LAD26NM,CTYUA26CD,CTYUA26NM,RGN26CD,RGN26NM,CTRY26CD,CTRY26NM',
        returnGeometry='false', returnDistinctValues='true', orderByFields='LAD26CD',
        resultRecordCount=2000, f='json'), timeout=45)
    response.raise_for_status()
    payload = response.json()
    if 'error' in payload or payload.get('exceededTransferLimit'):
        raise ValueError('Official reference incomplete')
    records = [feature['attributes'] for feature in payload['features']]
    if not 300 <= len(records) <= 450:
        raise ValueError('Unexpected administrative catalogue size')
    areas, edges = {}, set()
    def area(code, name, kind):
        if not code or not name or '99999999' in code:
            return None
        existing = areas.get(code)
        row = dict(code=code, name=name, kind=kind)
        if existing and existing != row:
            raise ValueError('Contradictory official area identity: '+code)
        areas[code] = row
        return code
    def edge(child, parent):
        if child and parent and child != parent:
            edges.add((child, parent))
    for row in records:
        country = area(row['CTRY26CD'], row['CTRY26NM'], 'nation')
        region = area(row.get('RGN26CD'), row.get('RGN26NM'), 'region')
        council = area(row['LAD26CD'], row['LAD26NM'], 'council')
        county_code = row.get('CTYUA26CD')
        county = area(county_code, row.get('CTYUA26NM'), 'county') if county_code and county_code.startswith('E10') else None
        edge(region, country)
        edge(county, region or country)
        edge(council, county or region or country)
    gb = [postcode for postcode, _, _ in SAMPLES if not postcode.startswith('BT')]
    response = requests.post('https://api.postcodes.io/postcodes', json={'postcodes': gb}, timeout=45)
    response.raise_for_status()
    result = response.json()
    if result.get('status') != 200 or len(result['result']) != len(gb):
        raise ValueError('Incomplete postcode lookup')
    looked_up = {item['query']: item['result'] for item in result['result']}
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    postcodes, cases = [], []
    for index, (postcode, label, tag) in enumerate(SAMPLES):
        case = dict(id=f'geo-{index+1:02}', postcode=postcode, label=label, tag=tag,
                    radius_km=10, ages=[0, 5], expected_behaviour='Nearby eligible content or honest empty state; request failure is unavailable')
        cases.append(case)
        if postcode.startswith('BT'):
            case.update(state='blocked_licence', expected_nation='Northern Ireland',
                        reason='NI postcode geocodes withheld pending authorised commercial data basis')
            continue
        item = looked_up[postcode]
        if not item or item['codes']['admin_district'] not in areas:
            raise ValueError('Unqualified postcode: '+postcode)
        nations = [a['code'] for a in areas.values() if a['kind']=='nation' and a['name']==item['country']]
        if len(nations) != 1: raise ValueError('Unqualified postcode nation')
        row = dict(postcode=item['postcode'], latitude=item['latitude'], longitude=item['longitude'],
                   council_code=item['codes']['admin_district'], nation_code=nations[0],
                   region_code=item['codes'].get('region'), county_code=item['codes'].get('admin_county'),
                   introduced=item.get('date_of_introduction'), terminated=None,
                   coordinate_method='Postcodes.io postcode representative point', source='https://api.postcodes.io/postcodes',
                   observed_at=now)
        if row['region_code'] not in areas: row['region_code'] = None
        if row['county_code'] not in areas: row['county_code'] = None
        postcodes.append(row)
        case.update(state='reference_verified', expected_nation=item['country'],
                    expected_council=item['admin_district'], expected_council_code=row['council_code'],
                    expected_region=item.get('region'), latitude=row['latitude'], longitude=row['longitude'])
    pack = dict(version=1, captured_at=now, scope='30 deliberate scenarios, not a statistical national coverage sample',
                cases=cases, negative_cases=[
                    dict(id='invalid', input='NOT A POSTCODE', expected='Reject or no match; never invent coordinates'),
                    dict(id='terminated', input='fixture-only terminated postcode', expected='Reference retains termination; current lookup must not silently use as live'),
                    dict(id='permission_denied', input=None, expected='Manual location selection remains available'),
                    dict(id='no_location', input=None, expected='National content; no inherited visitor location'),
                    dict(id='lookup_outage', input='W3 9LN', expected='Unavailable, not empty content'),
                    dict(id='radius_boundary', input='synthetic points at 9.999 and 10.001 km', expected='Inside included, outside excluded independent of council boundary'),
                ])
    reference = dict(version=1, release_id='ons-may-2026-sample-20261018', captured_at=now,
        administrative=dict(**pinned, scope='UK council catalogue and applicable higher areas',
                            response_sha256=hashlib.sha256(response_bytes(records)).hexdigest()),
        postal=dict(source='https://postcodes.io/docs/licences/', scope='28 GB sample postcodes only; no NI geocodes',
                    licence='OS OpenData terms for GB postcode data',
                    attribution=['Contains Ordnance Survey data © Crown copyright and database right 2025.',
                                 'Contains Royal Mail data © Royal Mail copyright and database right 2025.',
                                 'Contains National Statistics data © Crown copyright and database right 2025.',
                                 'Contains NRS data © Crown copyright and database right 2025.']),
        areas=sorted(areas.values(), key=lambda row: row['code']),
        relationships=[dict(child=child, parent=parent, kind='administrative') for child, parent in sorted(edges)],
        postcodes=postcodes)
    (ROOT/'geography/reference.json').write_text(json.dumps(reference, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    (ROOT/'geography/test-pack.json').write_text(json.dumps(pack, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps(dict(areas=len(areas), councils=sum(r['kind']=='council' for r in areas.values()),
                         postcodes=len(postcodes), scenarios=len(cases), ni_geocodes=0)))


def response_bytes(records):
    return json.dumps(records, sort_keys=True, separators=(',', ':')).encode()


if __name__ == '__main__':
    main()

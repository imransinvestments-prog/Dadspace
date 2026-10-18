"""Read-only, reproducible pilot evidence. Never invent ages or venue matches."""
import math
import re

PILOT = (51.508924, -0.275866)
POSTCODE = re.compile(r'\b([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})\b', re.I)


def full_postcode(value):
    match = POSTCODE.search(value or '')
    return (match[1] + match[2]).upper() if match else None


def age_evidence(value):
    text = (value or '').strip().lower().replace('½','.5').replace('–','-').replace('—','-')
    if not text:
        return {'state':'unknown','reason':'missing age'}
    # Developmental labels evidence early-years suitability, not an invented age.
    if re.fullmatch(r'(?:for )?(?:bab(?:y|ies)(?:\s*(?:and|,|or|/)\s*toddlers?)?|toddlers?|pre-?school(?:ers)?|newborns?(?: to sitting unaided)?|sitting (?:to|until) confident(?:ly)? walking)',text):
        return {'state':'eligible','reason':'explicit early-years label','evidence':value}
    if re.search(r'\byear\s*\d|school age|school aged|confident walking|pregnant|whole family',text):
        return {'state':'unknown','reason':'unbounded or school/developmental wording','evidence':value}
    # Only a whole-field numeric age expression qualifies; unrelated digits do not.
    text = re.sub(r'^(?:ages?|aged|for)\s+','',text)
    text = text.replace('mths','months').replace('mth','month').replace('yrs','years').replace('yr','year')
    endpoint = r'(\d+(?:\.\d+)?)(?:\s*(weeks?|months?|years?))?'
    under = re.fullmatch(r'(?:under|up to)\s+(\d+(?:\.\d+)?)(?:\s*(years?|months?|weeks?))?s?',text)
    if under:
        upper = float(under[1]) / (12 if under[2] and under[2].startswith('month') else 52 if under[2] and under[2].startswith('week') else 1)
        return {'state':'eligible' if upper>0 else 'unknown','reason':'explicit upper age limit','evidence':value}
    pair = re.fullmatch(endpoint+r'\s*(?:-|to)\s*'+endpoint,text)
    plus = re.fullmatch(endpoint+r'\s*\+\s*(years?|months?|weeks?)?',text)
    if not pair and not plus:
        return {'state':'unknown','reason':'age expression requires review','evidence':value}
    if pair:
        first, unit_a, second, unit_b = pair.groups()
        unit_a = unit_a or unit_b or 'years'
        unit_b = unit_b or unit_a
        lower = float(first)/(12 if unit_a.startswith('month') else 52 if unit_a.startswith('week') else 1)
        upper = float(second)/(12 if unit_b.startswith('month') else 52 if unit_b.startswith('week') else 1)
        if upper < lower:
            return {'state':'unknown','reason':'contradictory age range','evidence':value}
    else:
        first,unit_a,unit_b=plus.groups()
        unit_a=unit_a or unit_b or 'years'
        lower=float(first)/(12 if unit_a.startswith('month') else 52 if unit_a.startswith('week') else 1)
        upper=None
    # Ages 0–5 inclusive means younger than the sixth birthday; overlap only.
    return {'state':'eligible' if lower<6 else 'outside','minimum_years':lower,
            'maximum_years':upper,'reason':'explicit numeric restriction','evidence':value}


def valid_point(lat,lng):
    return (type(lat) in (float,int) and type(lng) in (float,int)
            and math.isfinite(lat) and math.isfinite(lng) and -90<=lat<=90 and -180<=lng<=180)


def distance_km(point):
    a,b=map(math.radians,PILOT); c,d=map(math.radians,point)
    h=math.sin((c-a)/2)**2+math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2
    return 6371*2*math.asin(min(1,math.sqrt(h)))


def location_evidence(row,postcodes):
    if re.search(r'\b(?:online|virtual|multiple venues|various locations|tbc|tba)\b',row.get('location') or '',re.I):
        return {'state':'unknown','method':'delivery_mode_or_location_requires_review'}
    if row.get('venue_public_visible') is True and valid_point(row.get('venue_latitude'),row.get('venue_longitude')):
        point=(row['venue_latitude'],row['venue_longitude'])
        method='public_canonical_venue'
    else:
        postcode=full_postcode(row.get('postcode')) or full_postcode(row.get('location'))
        hit=postcodes.get(postcode,{})
        if not valid_point(hit.get('latitude'),hit.get('longitude')):
            return {'state':'unknown','method':'unresolved_postcode_or_location','postcode':postcode}
        point=(hit['latitude'],hit['longitude']);method=hit.get('method','published_full_postcode')
    distance=distance_km(point)
    state='local' if distance<=10 else 'outside'
    if method=='existing_public_venues_same_full_postcode' and abs(distance-10)<0.25:
        state='unknown'
    return {'state':state,'method':method,
            'latitude':point[0],'longitude':point[1],'distance_km':round(distance,6)}


def build_ledger(snapshot,postcodes):
    rows=[]; identities={}
    for original in snapshot['rows']:
        key=original.get('identity_key') or original.get('dedupe_key') or original['id']
        if key in identities:
            identities[key]['duplicate_row_ids'].append(original['id'])
            continue
        age=age_evidence(original.get('age_range')); location=location_evidence(original,postcodes)
        row={**original,'duplicate_row_ids':[],'age_evidence':age,'location_evidence':location,
             'pilot_eligible':age['state']=='eligible' and location['state']=='local'}
        identities[key]=row;rows.append(row)
    eligible=[r for r in rows if r['pilot_eligible']]
    review=[]
    for predicate in (lambda r:r['pilot_eligible'],lambda r:r['location_evidence']['state']=='local' and r['age_evidence']['state']=='unknown',
                      lambda r:r['location_evidence']['state']=='unknown' and r['age_evidence']['state']=='eligible',
                      lambda r:r['age_evidence']['state']=='outside'):
        review.extend([r['id'] for r in rows if predicate(r)][:2])
    return {'captured_at':snapshot['captured_at'],'pilot':{'postcode':'W3 9LN','latitude':PILOT[0],
        'longitude':PILOT[1],'radius_km':10,'ages':'0–5 inclusive; evidenced overlap before sixth birthday'},
        'input_count':len(snapshot['rows']),'unique_opportunities':len(rows),
        'pilot_eligible_count':len(eligible),'unknown_location_count':sum(r['location_evidence']['state']=='unknown' for r in rows),
        'unknown_age_count':sum(r['age_evidence']['state']=='unknown' for r in rows),
        'eligible_provider_ids':sorted({r['source_id'] for r in eligible if r['source_id']}),
        'eligible_categories':sorted({r['category'] or 'unknown' for r in eligible}),
        'review_ids':list(dict.fromkeys(review)),
        'limits':['Eligibility evidence is not owner quality acceptance (#136).',
            'City-only/free-text locations remain unresolved; public search may use broader geocoding.',
            'Same-postcode public venue coordinates are approximate; ambiguous spreads remain unresolved. No outward-code fallback or invented venue relationship.',
            'Unknown and national/wider-age rows are retained; duplicate identity is collapsed only within this report.'],
        'rows':rows}

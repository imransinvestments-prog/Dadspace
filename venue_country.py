"""UK nation evidence from exact postcode lookups, never from venue names."""
from __future__ import annotations
import datetime as dt
import json
import re
import urllib.request

API = 'https://api.postcodes.io/postcodes'
DISTRICT_NATIONS = {'E06': 'England', 'E07': 'England', 'E08': 'England', 'E09': 'England',
                    'S12': 'Scotland', 'W06': 'Wales', 'N09': 'Northern Ireland'}

def normalize_postcode(value):
    return re.sub(r'\s+', '', (value or '').upper())

def lookup_postcodes(postcodes):
    """Bounded batches; failures remain unknown and never erase stored countries."""
    values = sorted({normalize_postcode(p) for p in postcodes if normalize_postcode(p)})
    results = {}
    for offset in range(0, len(values), 100):
        batch = values[offset:offset + 100]
        try:
            request = urllib.request.Request(API, data=json.dumps({'postcodes': batch}).encode(),
                headers={'Content-Type': 'application/json', 'User-Agent': 'DadspaceVenueBot/2.0'})
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.load(response)
            entries = data.get('result') or []
            if data.get('status') != 200 or {normalize_postcode(e['query']) for e in entries} != set(batch):
                raise ValueError('Incomplete postcode response')
            results.update({normalize_postcode(e['query']): e['result'] for e in entries})
        except (OSError, ValueError, KeyError, TypeError):
            results.update({p: {'_error': 'lookup_unavailable'} for p in batch})
    return results

def resolve_country(postcode, result, authority_code=None):
    """Require exact postcode and matching GSS district geography; conflict => unknown."""
    evidence = {'source_url': API, 'postcode': postcode, 'country': None,
                'checked_at': dt.datetime.now(dt.timezone.utc).isoformat()}
    normalized = normalize_postcode(postcode)
    if not normalized:
        evidence['reason'] = 'missing_postcode'
    elif not result:
        evidence['reason'] = 'postcode_not_found'
    elif result.get('_error'):
        evidence['reason'] = 'lookup_unavailable'
    elif normalize_postcode(result.get('postcode')) != normalized:
        evidence['reason'] = 'postcode_response_mismatch'
    else:
        code = (result.get('codes') or {}).get('admin_district') or ''
        country = DISTRICT_NATIONS.get(code[:3]) if re.fullmatch(r'[ESWN]\d{8}', code) else None
        evidence.update(admin_district_code=code, validated_postcode=result.get('postcode'))
        if not country or country != result.get('country'):
            evidence['reason'] = 'unsupported_or_conflicting_country'
        elif authority_code and re.fullmatch(r'[ESWN]\d{8}', authority_code) and authority_code[0] != code[0]:
            evidence['reason'] = 'source_authority_country_conflict'
        else:
            evidence.update(country=country, reason='exact_postcode_and_geography')
    return evidence

def enrich_country_candidate(candidate, results):
    payload = candidate.get('payload') or {}
    authority = next((v for k, v in payload.items() if k.lower() == 'reporting service code'), None)
    evidence = resolve_country(candidate.get('postcode'), results.get(normalize_postcode(candidate.get('postcode'))), authority)
    candidate['country'] = evidence['country']
    candidate['payload'] = {**payload, '_dadspace_country': evidence}
    return candidate

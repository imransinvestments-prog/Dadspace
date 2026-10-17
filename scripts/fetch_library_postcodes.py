"""Owner-authorized public library postcode lookup; never writes the database."""
import datetime as dt
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
COHORT = ROOT / 'artefacts/data/places-data-cohort-2026-10-17.json'
OUTPUT = ROOT / 'artefacts/data/library-postcode-evidence-2026-10-17.json'

def normalize(value):
    return re.sub(r'\s+', '', (value or '').upper())

def main():
    rows = json.loads(COHORT.read_text(encoding='utf-8'))['libraries']
    postcodes = sorted({normalize(r['postcode']) for r in rows if normalize(r['postcode'])}
        | {'SW1A1AA', 'EH11YZ', 'CF101EP', 'BT15GS'})
    saved = json.loads(OUTPUT.read_text(encoding='utf-8')) if OUTPUT.exists() else {
        'retrieved_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'source': 'https://api.postcodes.io/postcodes',
        'documentation': 'https://postcodes.io/docs/postcode/bulk/',
        'results': {},
    }
    missing = [p for p in postcodes if p not in saved['results']]
    for offset in range(0, len(missing), 100):
        batch = missing[offset:offset + 100]
        request = urllib.request.Request(saved['source'], data=json.dumps({'postcodes': batch}).encode(),
            headers={'Content-Type': 'application/json', 'User-Agent': 'DadspaceDataReview/1.0'})
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.load(response)
        if payload.get('status') != 200 or len(payload['result']) != len(batch):
            raise RuntimeError('Incomplete postcode response; no database writes performed')
        for entry in payload['result']:
            result = entry['result']
            saved['results'][normalize(entry['query'])] = None if result is None else {
                'postcode': result['postcode'], 'country': result['country'],
                'codes': {'admin_district': (result.get('codes') or {}).get('admin_district')},
            }
        OUTPUT.write_text(json.dumps(saved, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
        print(f'Cached {len(saved["results"])} / {len(postcodes)} postcode results', flush=True)

if __name__ == '__main__':
    main()

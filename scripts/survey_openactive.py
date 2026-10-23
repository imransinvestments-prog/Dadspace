"""Read-only OpenActive coverage survey. No Gemini calls or database writes.

python scripts/survey_openactive.py --output artefacts/data/openactive-survey-YYYY-MM-DD.json
Hosts are walked in parallel, but each host sequentially and politely. Supply found
here stays an inactive candidate until licence, attribution and mapping are approved.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import openactive


def survey_host(entries, args, postcodes):
    client = openactive.Client(delay=args.delay)
    return [openactive.survey_dataset(entry, client, args.max_pages, args.seconds, postcodes) for entry in entries]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--match', default='', help='only datasets whose URL contains this text')
    parser.add_argument('--max-pages', type=int, default=2000, help='per feed')
    parser.add_argument('--seconds', type=int, default=900, help='per dataset')
    parser.add_argument('--delay', type=float, default=1.0, help='seconds between requests to one provider')
    parser.add_argument('--no-postcodes', action='store_true', help='skip postcodes.io centroids for feeds without coordinates')
    args = parser.parse_args()
    client = openactive.Client(delay=args.delay)
    entries = openactive.dataset_urls(client.get(openactive.CATALOGUE).json(), client)
    entries = [e for e in entries if args.match in e.get('url', e['catalogue'])]
    if args.limit:
        entries = entries[:args.limit]
    hosts = {}
    for entry in entries:
        hosts.setdefault(openactive.host_group(entry.get('url') or entry['catalogue']), []).append(entry)
    postcodes = None if args.no_postcodes else openactive.Postcodes()
    with ThreadPoolExecutor(max_workers=8) as pool:
        datasets = [d for group in pool.map(lambda e: survey_host(e, args, postcodes), hosts.values()) for d in group]
    datasets.sort(key=lambda d: -(d.get('summary') or {}).get('pilot_eligible', -1))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {'ai_calls': 0, 'database_writes': 0, 'catalogue': openactive.CATALOGUE,
              'totals': openactive.totals(datasets), 'datasets': datasets}
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report['totals'], indent=2, ensure_ascii=False))
    for d in datasets[:25]:
        s = d.get('summary') or {}
        print(f"{s.get('pilot_eligible', '-'):>6} {s.get('local', '-'):>6} {s.get('series', '-'):>7}  {d.get('name') or d.get('url')}  {d.get('error') or ''}")


if __name__ == '__main__':
    main()

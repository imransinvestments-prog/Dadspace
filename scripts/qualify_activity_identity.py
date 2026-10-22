"""Bounded, read-only MyLibrary session identity evidence; never activates a source."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from library_portal import published_records

URL = 'https://libraries.ealing.gov.uk/events'
HOST = 'ealing.events.mylibrary.digital'


def positive_id(value):
    if type(value) is not int or value <= 0:
        raise ValueError('Missing/invalid numeric provider identity')
    return value


def identity_facts(records):
    """Series is a session container, not an inferred cross-series programme."""
    groups = {}
    seen = {}
    for record in records:
        if not record.get('series_id'):
            continue
        eid = positive_id(record.get('event_id'))
        sid = positive_id(record.get('series_id'))
        link = urlparse(record.get('url', ''))
        if (link.scheme != 'https' or link.hostname != HOST or link.path != '/event'
                or link.username or link.password or link.port not in (None, 443)
                or parse_qs(link.query) != {'id': [str(eid)]} or link.fragment):
            raise ValueError('Occurrence URL contradicts provider ID')
        fact = {key: record.get(key) for key in ('event_id', 'series_id', 'name',
                'location_id', 'location_name', 'start_time', 'end_time', 'url',
                'recurring_dates_tagline')}
        if eid in seen and seen[eid] != fact:
            raise ValueError('Contradictory occurrence identity')
        seen[eid] = fact
        groups.setdefault(sid, {})[eid] = fact
    return {str(sid): sorted(items.values(), key=lambda r: r['event_id'])
            for sid, items in sorted(groups.items()) if len(items) >= 2}


def qualify(first, second):
    a, b = identity_facts(first), identity_facts(second)
    # Frozen, previously captured family series: no estate-wide qualification.
    selected = ['264038', '319285']
    evidence = []
    for sid in selected:
        if sid not in a or sid not in b or a[sid] != b[sid]:
            raise ValueError('Selected series missing, incomplete or changed between passes')
        evidence.append({'namespace': HOST, 'session_id': sid, 'programme_id': None,
                         'occurrences': a[sid]})
    return {'source_url': URL, 'selected_series': evidence,
            'scope': 'Two observed public series; not full index completeness or long-term stability',
            'policy': 'Host-scoped numeric series identifies a session container; event_id identifies an occurrence. Cross-series programme identity remains unknown.',
            'production_adoption': False, 'model_calls': 0, 'database_writes': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    import worker
    passes, hashes, timestamps = [], [], []
    for _ in range(2):
        allowed, reason = worker.robots_allows(URL)
        if not allowed:
            raise RuntimeError(reason)
        html = worker.fetch_html_requests(URL)
        timestamps.append(dt.datetime.now(dt.timezone.utc).isoformat())
        hashes.append(hashlib.sha256(html.encode()).hexdigest())
        passes.append(published_records(html))
    report = qualify(*passes)
    report.update(captured_at=timestamps, page_hashes=hashes,
                  index_record_counts=[len(rows) for rows in passes])
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'sessions': len(report['selected_series']),
                      'occurrences': [len(s['occurrences']) for s in report['selected_series']],
                      'model_calls': 0, 'database_writes': 0, 'activation': False}))


if __name__ == '__main__':
    main()

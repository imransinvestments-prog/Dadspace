"""Read-only qualification of the owner-reviewed Sutton passing subset.

No database credentials, source activation or AI extraction. Default execution
uses the unmodified normal worker and its production browser renderer.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['DRY_RUN'] = 'true'
os.environ['ALLOW_VENUE_WRITES'] = 'false'
import events_worker
import worker

# Deliberately bounded programme routes, not borough/index completeness.
SOURCES = [
    ('Sutton Central Rhymetime', '361652'),
    ('Wallington Rhymetime', '366731'),
    ('Circle Rhymetime', '382091'),
    ('Cheam Rhymetime', '353033'),
    ('Westcroft Rhymetime', '354254'),
    ('Tweedale Stay & Play', '374590'),
]


def comparable(row):
    return {key: value for key, value in row.items()
            if key not in ('last_seen_at', 'last_verified_at')}


def acceptance_errors(results):
    errors = []
    for name, event_id in SOURCES:
        passes = [result for result in results if result['event_id'] == event_id]
        if len(passes) != 2 or {p['attempt'] for p in passes} != {1, 2}:
            errors.append(name + ': two distinct passes required')
            continue
        if any(p['status'] != 'ok' or len(p['rows']) != 1 for p in passes):
            errors.append(name + ': both passes must accept one programme')
            continue
        rows = [p['rows'][0] for p in passes]
        if any(not row.get('dedupe_key') for row in rows):
            errors.append(name + ': missing identity')
        if comparable(rows[0]) != comparable(rows[1]):
            errors.append(name + ': identity or content changed between passes')
        if any(p['stats'].get('gemini_logical_calls') != 0 for p in passes):
            errors.append(name + ': unexpected model usage')
        if event_id == '374590' and any('London Borough of Sutton only' not in row.get('description', '') for row in rows):
            errors.append(name + ': resident restriction missing')
    keys = [p['rows'][0].get('dedupe_key') for p in results
            if p['attempt'] == 1 and len(p['rows']) == 1]
    if len(keys) != len(set(keys)):
        errors.append('Duplicate programme identities across reviewed sources')
    return errors


def main():
    worker.DRY_RUN = True
    results = []
    path = ROOT / 'sutton-source-review/results.json'
    path.parent.mkdir(exist_ok=True)
    today = worker.today_uk()
    for name, event_id in SOURCES:
        source = dict(id='preview-sutton-' + event_id, name=name,
                      url='https://events.sutton.gov.uk/event?id=' + event_id,
                      source_adapter='mylibrary_calendar', collection_days=30)
        for attempt in (1, 2):
            status, rows, digest, message, stats = events_worker.process_source(source, None, today)
            results.append(dict(name=name, event_id=event_id, url=source['url'],
                                attempt=attempt, status=status, rows=rows,
                                page_hash=digest, message=message, stats=stats))
            print(name, attempt, status, len(rows), message, flush=True)
            path.write_text(json.dumps(dict(
                checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                as_of=today.isoformat(), database_writes=0, model_calls=0,
                production_enabled=False, borough_coverage_complete=False,
                route='normal worker; production browser renderer',
                results=results, acceptance_errors=acceptance_errors(results)), indent=2), encoding='utf-8')
    errors = acceptance_errors(results)
    if errors:
        raise SystemExit('\n'.join(errors))


if __name__ == '__main__':
    main()


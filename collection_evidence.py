"""Append-only collection evidence. No database writes or freshness decisions.

Validated rows, successful writes and public membership are separate outcomes.
Unknown coverage is never inferred from a green job or an unchanged root hash.
"""
import datetime as dt
import json
import os
from pathlib import Path


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def public_view_readback(db, source_id, rows, *, limit=20):
    """Bounded SELECT of public-view membership, not anonymous access certification.

    Keys changed by the database identity trigger may be unmatched; do not call
    them unpublished or infer a deletion. Full/browser acceptance is separate.
    """
    keys = sorted({str(row['dedupe_key']) for row in rows if row.get('dedupe_key')})
    selected = keys[:limit]
    result = {'state': 'not_checked', 'requested_keys': selected,
              'candidate_count': len(keys), 'sample_complete': len(keys) <= limit,
              'rows': None, 'unmatched_keys': None}
    if not selected:
        return result
    try:
        response = (db.table('current_activities')
            .select('id,dedupe_key,source_id,last_seen_at,event_url')
            .eq('source_id', source_id).in_('dedupe_key', selected).limit(limit).execute())
        if not isinstance(response.data, list):
            raise ValueError('Unavailable public view response')
        found = {row.get('dedupe_key') for row in response.data}
        result.update(state='read', rows=response.data,
                      unmatched_keys=[key for key in selected if key not in found])
    except Exception:
        # No raw database/credential-bearing error strings in evidence artifacts.
        result['state'] = 'unavailable'
    return result


class CollectionEvidence:
    def __init__(self, sources, *, dry_run, path=None):
        self.path = Path(path) if path else None
        self.dry_run = dry_run
        self.expected = [str(s['id']) for s in sources]
        self.observed = set()
        self.outcomes = []
        self.run = {key: os.environ.get(name) for key, name in (
            ('run_id', 'GITHUB_RUN_ID'), ('attempt', 'GITHUB_RUN_ATTEMPT'),
            ('sha', 'GITHUB_SHA'), ('event', 'GITHUB_EVENT_NAME'))}
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # A restarted invocation must not silently mix two runs in one file.
            with self.path.open('x', encoding='utf-8') as stream:
                stream.write(json.dumps({'kind': 'start', 'at': utc_now(),
                    'run': self.run, 'dry_run': dry_run,
                    'expected_source_ids': self.expected}) + '\n')

    def append(self, record):
        if self.path:
            with self.path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(record, ensure_ascii=False) + '\n')
                stream.flush()
                os.fsync(stream.fileno())

    def source(self, source, status, stats, rows, *, write_state, health_state, readback=None):
        source_id = str(source['id'])
        if source_id not in self.expected or source_id in self.observed:
            raise ValueError('Unexpected or duplicate source evidence')
        extracted = stats.get('extracted')
        qualified = stats.get('kept', len(rows) if status in ('ok', 'ok_zero') else None)
        duplicates = stats.get('duplicates', 0)
        rejected = (max(0, extracted - qualified - duplicates)
                    if isinstance(extracted, int) and isinstance(qualified, int) else None)
        record = {'kind': 'source', 'at': utc_now(), 'source_id': source_id,
            'status': status, 'extracted': extracted, 'validated': qualified,
            'rejected': rejected, 'merged_duplicates': duplicates,
            'write_state': write_state, 'health_state': health_state,
            'saved_count': len(rows) if write_state == 'succeeded' else None,
            'unchanged': status == 'unchanged',
            'deferred': status.startswith('deferred'),
            'failed': status.startswith('failed') or status == 'fatal',
            'suspicious_zero': status == 'ok_zero',
            'coverage': (stats.get('item_coverage') or
                         ('not_checked' if status.startswith('deferred') else 'unknown')),
            'public_readback': readback or {'state': 'not_checked'},
            'candidate_keys': sorted({str(r['dedupe_key']) for r in rows if r.get('dedupe_key')})}
        self.append(record)
        self.observed.add(source_id)
        self.outcomes.append(record)

    def finish(self, *, stopped_early, fatal):
        missing = [key for key in self.expected if key not in self.observed]
        for source_id in missing:
            self.source({'id': source_id}, 'deferred_not_processed', {}, [],
                        write_state='not_attempted', health_state='not_attempted')
        summary = {'kind': 'finish', 'at': utc_now(), 'run': self.run,
            'expected_sources': len(self.expected), 'recorded_sources': len(self.observed),
            'not_processed_source_ids': missing, 'stopped_early': stopped_early,
            'fatal': fatal, 'all_sources_checked': not missing and not any(
                row['deferred'] for row in self.outcomes),
            'all_sources_succeeded': not missing and not fatal and all(
                row['status'] in ('ok', 'ok_zero', 'unchanged')
                and row['health_state'] in ('succeeded', 'dry_run') for row in self.outcomes)}
        self.append(summary)
        return summary

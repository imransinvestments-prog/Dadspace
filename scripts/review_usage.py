"""Bounded paired source comparison; no DB credentials or cache writes."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.append(str(ROOT / 'provider-code'))
os.environ['DRY_RUN'] = 'true'
import worker
import events_worker
import gemini_usage
from llm_provider import make_extractor

BASELINE = '772a0754f8160113fce30533f8ce3ad086e98b73'
SOURCES = [('Cardiff Libraries', 'https://cardiffhubs.co.uk/events/'),
           ('Museum Wales', 'https://museum.wales/whatson/')]
FIELDS = ('title', 'start_date', 'end_date', 'schedule_text', 'time_text', 'location',
          'venue_name', 'venue_address', 'postcode', 'event_url', 'cost_text', 'age_range',
          'recurrence', 'category', 'listing_type')


def main():
    events_worker.install_quality_rules()
    events_worker._venue_client = lambda: None
    # Review the current preparation with the same shared OpenAI adapter/schema
    # as #69. This explicit manual job does not activate that provider in workers.
    gemini_usage.make_extractor = make_extractor
    code = subprocess.check_output(['git', 'show', BASELINE + ':worker.py'], cwd=ROOT).decode('utf-8')
    old = {'__name__': 'baseline_worker'}
    exec(compile(code, '<baseline_worker>', 'exec'), old)
    output = ROOT / 'usage-review'
    output.mkdir(exist_ok=True)
    caller = events_worker.make_gemini_caller()
    report = {'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'baseline': BASELINE,
              'database_access': False, 'database_writes': 0, 'settings': caller.settings, 'sources': []}
    try:
        for index, (name, url) in enumerate(SOURCES):
            allowed, reason = worker.robots_allows(url)
            if not allowed:
                raise RuntimeError(reason)
            documents = [(url, worker.fetch_html_requests(url))]
            (output / f'{index}-snapshot.json').write_text(json.dumps({'url': url, 'documents': documents}), encoding='utf-8')
            source = {'id': 'preview-' + name, 'name': name, 'url': url}
            result = {'source': name, 'variants': {}}
            report['sources'].append(result)
            for variant, prepare in [('before', old['prepare_content']), ('after', worker.prepare_content)]:
                content, method = prepare(documents, url)
                prompt = worker.build_prompt(source, url, content, worker.today_uk())
                (output / f'{index}-{variant}-prepared.txt').write_text(content, encoding='utf-8')
                before = dict(caller.metrics)
                raw = caller(prompt)
                stats = {}
                rows = worker.clean_events(raw, source, url, method, worker.today_uk(), stats)
                result['variants'][variant] = {'chars': len(content), 'sha256': hashlib.sha256(content.encode()).hexdigest(),
                    'at_limit': len(content) >= worker.MAX_CHARS, 'raw': raw, 'rows': rows, 'validation': stats,
                    'usage': {key: caller.metrics[key] - before.get(key, 0) for key in caller.metrics}}
                report['metrics'] = dict(caller.metrics)
                (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            def keyed(variant):
                return {(r['event_url'], r.get('listing_type'), r.get('start_date')):
                        {f: r.get(f) for f in FIELDS} for r in result['variants'][variant]['rows']}
            before, after = keyed('before'), keyed('after')
            result['comparison'] = {'missing': [list(k) for k in before.keys() - after.keys()],
                'added': [list(k) for k in after.keys() - before.keys()],
                'changed_fields': [{ 'listing': list(k), 'fields': [f for f in FIELDS if before[k][f] != after[k][f]]}
                                   for k in before.keys() & after.keys() if before[k] != after[k]]}
            print(json.dumps({'source': name, 'before_accepted': len(before), 'after_accepted': len(after),
                              'comparison': result['comparison']}), flush=True)
    finally:
        report['metrics'] = dict(caller.metrics)
        (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        caller.close()


if __name__ == '__main__':
    main()

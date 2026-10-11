"""Three bounded real-source extractions, preserving evidence without DB access."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['DRY_RUN'] = 'true'
import events_worker
import worker as base

PILOT = ('Kent Libraries', 'Cardiff Libraries', 'Museum Wales')


def main():
    base.DRY_RUN = True
    events_worker.install_quality_rules()
    # This review intentionally does not resolve/create database venue records.
    events_worker._venue_client = lambda: None
    sources = json.loads((ROOT / 'artefacts/data/activities-source-candidates.json').read_text(encoding='utf-8'))
    extract = base.make_gemini_caller()
    output = ROOT / 'llm-source-review'
    output.mkdir(exist_ok=True)
    report = {'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'database_access': False, 'database_writes': 0,
              'settings': extract.settings, 'results': []}
    build_prompt = base.build_prompt
    state = {}

    def snapshot_prompt(source, url, content, today):
        state['content'] = content
        state['prompt'] = build_prompt(source, url, content, today)
        return state['prompt']

    def capture(prompt):
        state['raw'] = extract(prompt)
        return state['raw']
    capture.metrics = extract.metrics
    base.build_prompt = snapshot_prompt
    try:
        for index, name in enumerate(PILOT):
            state.clear()
            source = dict(next(s for s in sources if s['name'] == name),
                          id='preview-' + name, last_hash=None, last_success_at=None)
            result = {'source': name, 'url': source['url']}
            try:
                status, rows, page_hash, message, stats = base.process_source(source, capture, base.today_uk())
                result.update(status=status, rows=rows, page_hash=page_hash, message=message, stats=stats)
                # These are review flags, not a replacement for existing validation.
                content = state.get('content', '')
                result['unquoted_listing_urls'] = [r.get('event_url') for r in rows
                    if r.get('event_url') and r['event_url'] not in content]
            except (base.FatalError, base.BudgetExhausted) as exc:
                result.update(status='stopped', error=str(exc))
                report['results'].append(result)
                raise
            except Exception as exc:
                result.update(status='failed', error=str(exc))
            finally:
                if state.get('content'):
                    (output / f'{index + 1}-prepared.txt').write_text(state['content'], encoding='utf-8')
                    (output / f'{index + 1}-prompt.txt').write_text(state['prompt'], encoding='utf-8')
                    result['prepared_sha256'] = hashlib.sha256(state['content'].encode()).hexdigest()
                if 'raw' in state:
                    result['raw'] = state['raw']
                if result not in report['results']:
                    report['results'].append(result)
                report['metrics'] = dict(extract.metrics)
                (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
                print(json.dumps({'source': name, 'status': result['status'],
                                  'accepted': len(result.get('rows', [])),
                                  'message': result.get('message', result.get('error'))}), flush=True)
    finally:
        extract.close()
        base.build_prompt = build_prompt
    print('LLM usage: ' + json.dumps(extract.metrics))
    if not any(r.get('rows') for r in report['results']):
        raise SystemExit('No accepted listings; inspect saved source and extraction evidence')


if __name__ == '__main__':
    main()

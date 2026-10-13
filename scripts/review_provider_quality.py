"""Four bounded Gemini/OpenAI calls against identical saved public pages.

No database credentials, cache persistence or publication. Cardiff is deliberately
one page: the separate public collection manifest records its full pagination.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['DRY_RUN'] = 'true'
import worker
import events_worker
from family_grounding import filter_grounded
from scripts.replay_shadow import compare

SOURCES = [('Cardiff Libraries', 'https://cardiffhubs.co.uk/events/'),
           ('Museum Wales', 'https://museum.wales/whatson/')]


def main():
    events_worker.install_quality_rules()
    events_worker._venue_client = lambda: None
    out = ROOT / 'provider-quality-review'
    out.mkdir(exist_ok=True)
    report = {'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'database_access': False, 'publishing': False, 'sources': [],
              'scope': 'Two saved listing pages; not full Cardiff or worker-wide acceptance',
              'total_tokens': 0, 'api_attempts': 0}
    documents = []
    for name, url in SOURCES:
        allowed, reason = worker.robots_allows(url)
        if not allowed:
            raise RuntimeError(reason)
        html = worker.fetch_html_requests(url)
        docs = [(url, html)]
        content, method = worker.prepare_content(docs, url, max_chars=0)
        if len(content) > 40000:
            raise ValueError(name + ' exceeds review input cap; narrow the review unit')
        (out / (name.replace(' ', '-') + '-snapshot.json')).write_text(
            json.dumps({'url': url, 'documents': docs}), encoding='utf-8')
        documents.append((name, url, docs, content, method))
    try:
        for name, url, docs, content, method in documents:
            source = {'id': 'review-' + name, 'name': name, 'url': url}
            result = {'source': name, 'variants': {}}
            report['sources'].append(result)
            prompt = worker.build_prompt(source, url, content, worker.today_uk())
            for provider, model in [('gemini', os.environ.get('GEMINI_MODEL') or 'gemini-3.6-flash'),
                                    ('openai', 'gpt-4.1-mini')]:
                if report['api_attempts'] >= 4 or report['total_tokens'] >= 80000:
                    raise RuntimeError('Shared comparison budget reached; remaining variants deferred')
                os.environ.update(EXTRACTION_LLM_PROVIDER=provider, EXTRACTION_LLM_MODEL=model,
                                  LLM_RUN_MAX_ATTEMPTS='1', LLM_MAX_RETRIES='0',
                                  LLM_RUN_TOKEN_BUDGET='80000', LLM_MAX_OUTPUT_TOKENS='10000')
                caller = events_worker.make_gemini_caller()
                try:
                    raw = caller(prompt)
                    stats = {}
                    grounded = filter_grounded(raw, docs, content, stats)
                    rows = worker.clean_events(grounded, source, url, method, worker.today_uk(), stats)
                    result['variants'][provider] = {'model': model, 'raw': raw, 'rows': rows,
                                                   'validation': stats, 'usage': dict(caller.metrics)}
                finally:
                    report['api_attempts'] += caller.metrics.get('api_attempts', 0)
                    report['total_tokens'] += caller.metrics.get('total_tokens', 0)
                    if caller.metrics.get('unknown_usage_attempts', 0):
                        report['unknown_usage'] = True
                    caller.close()
                    (out / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
                if report.get('unknown_usage'):
                    raise RuntimeError('Unknown request usage; defer further paid calls')
            result['comparison'] = compare(result['variants']['gemini']['rows'],
                                           result['variants']['openai']['rows'])
    finally:
        (out / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

"""Read-only access/detail audit. No Gemini calls or database writes.

python scripts/audit_activity_sources.py --output activity-source-audit.json
Access is not extraction validation; successful pages stay inactive candidates.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import events_worker
import worker as base
from activity_source_discovery import detail_urls, listing_html


def audit(source):
    result = dict(source)
    result['checked_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        allowed, reason = base.robots_allows(source['url'])
        result['robots_allowed'] = allowed
        if not allowed:
            result.update(status='blocked_robots', error=reason)
            return result
        html = listing_html(base.fetch_html_requests(source['url']))
        documents = [(source['url'], html)]
        if base.soft_404_title(documents):
            result.update(status='soft_404')
            return result
        content, method = base.prepare_content(documents, source['url'])
        result.update(status='accessible_pending_extraction', content_chars=len(content),
                      detail_urls=detail_urls(html, source['url']), method=method,
                      date_or_schedule_signals=len(base.DATE_HINT_PATTERN.findall(content)))
        result['excerpt'] = content[:1200]
        if len(content.strip()) < 200:
            result['status'] = 'insufficient_content'
    except Exception as exc:
        result.update(status='access_failed', error=str(exc)[:500])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--limit', type=int, default=0)
    args = parser.parse_args()
    events_worker.install_quality_rules()
    sources = json.loads((ROOT/'artefacts/data/activities-source-candidates.json').read_text())
    if args.limit:
        sources = sources[:args.limit]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(audit, sources))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'ai_calls':0,'database_writes':0,'sources':results}, indent=2), encoding='utf-8')
    for row in results:
        print(row['name'], row['status'], row.get('content_chars',0), len(row.get('detail_urls',[])))


if __name__ == '__main__':
    main()

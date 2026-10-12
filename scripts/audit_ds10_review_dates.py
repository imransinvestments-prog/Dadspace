"""Read-only bounded date/schedule audit of the frozen 100-activity review set."""
import concurrent.futures as futures
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import worker

ROOT=Path(__file__).resolve().parents[1]
SIGNAL=re.compile(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|fortnight|term.time|every month|weekly|first Saturday|[0-9]{1,2}:[0-9]{2}|[0-9]{1,2}\s*[ap]m)",re.I)

def main():
    rows=json.loads((ROOT/'artefacts/data/ds10-human-review-2026-10-11.json').read_text(encoding='utf-8'))['rows']
    urls=sorted({r['event_url'] for r in rows if r.get('event_url') and r['event_url'].startswith('https://')})
    cache=ROOT/'date-source-review';cache.mkdir(exist_ok=True)
    def fetch(url):
        result=dict(url=url,checked_at=dt.datetime.now(dt.timezone.utc).isoformat())
        try:
            allowed,reason=worker.robots_allows(url)
            if not allowed:return dict(result,status='robots_blocked',reason=reason)
            response=requests.get(url,headers={'User-Agent':'Mozilla/5.0 (compatible; DadspaceEventsBot/1.0)'},timeout=(5,15))
            result['http_status']=response.status_code
            response.raise_for_status()
            if urlparse(response.url).hostname!=urlparse(url).hostname:return dict(result,status='redirect_requires_review',target=response.url)
            response.encoding='utf-8'
            (cache/(hashlib.sha256(url.encode()).hexdigest()+'.html')).write_text(response.text,encoding='utf-8')
            soup=BeautifulSoup(response.text,'html.parser')
            result['page_title']=soup.h1.get_text(' ',strip=True) if soup.h1 else None
            root=soup.find('main') or soup.find('article') or soup
            for e in root.select('script,style,nav,header,footer'):e.decompose()
            texts=[p.get_text(' ',strip=True) for p in root.find_all(['p','li','time'])]
            snippets=list(dict.fromkeys(t for t in texts if SIGNAL.search(t)))[:8]
            result.update(status='readable',schedule_evidence=[t[:240] for t in snippets],has_schedule_evidence=bool(snippets))
        except Exception as exc:result.update(status='failed_fetch',reason=str(exc)[:300])
        print(result['status'],url,flush=True)
        return result
    with futures.ThreadPoolExecutor(max_workers=6) as pool:reports=list(pool.map(fetch,urls))
    index={r['url']:r for r in reports}
    output=dict(checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),database_writes=0,gemini_calls=0,note='Evidence signals require programme association/currentness review; readable alone is not qualified supply.',pages=reports,rows=[dict(id=r['id'],title=r['title'],url=r.get('event_url'),status=index.get(r.get('event_url'),{}).get('status','missing_detail_link')) for r in rows])
    path=ROOT/'artefacts/data/ds10-worksheet-date-audit-2026-10-12.json'
    path.write_text(json.dumps(output,indent=2),encoding='utf-8')
    print('Saved',len(reports),'pages covering',len(rows),'rows',flush=True)

if __name__=='__main__':main()

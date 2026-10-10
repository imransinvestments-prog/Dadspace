"""Bounded registry access evidence only; no database/model imports or writes."""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import time
import urllib.error
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urljoin

UA = 'DadspaceEventsBot/1.0'
MAX_BYTES = 2_000_000

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.text=[]; self.links=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip += 1
        if tag == 'a':
            href=dict(attrs).get('href')
            if href: self.links.append(href)
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self, data):
        if not self.skip and data.strip(): self.text.append(data.strip())

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml','Accept-Language':'en-GB'})
    with urllib.request.urlopen(req,timeout=12) as r:
        body=r.read(MAX_BYTES+1)
        return r.status,r.url,body[:MAX_BYTES].decode('utf-8',errors='replace'),len(body)>MAX_BYTES

def audit(s):
    start=time.monotonic()
    out={'id':s['id'],'name':s['name'],'url':s['url'],'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'request_budget':2}
    try:
        p=urlparse(s['url'])
        if p.scheme not in ('https','http') or not p.hostname: raise ValueError('Unsupported registry URL')
        robots_url=f'{p.scheme}://{p.netloc}/robots.txt'
        try:
            code,_,body,_=get(robots_url)
            rp=urllib.robotparser.RobotFileParser(); rp.parse(body.splitlines())
            out['robots_status']=code
            out['robots_allowed']=rp.can_fetch(UA,s['url'])
        except urllib.error.HTTPError as e:
            out['robots_status']=e.code
            out['robots_allowed']= e.code == 404
            if e.code != 404:
                out['status']='robots_unavailable'; return out
        except Exception as e:
            out.update(status='robots_unavailable',error=str(e)[:300]);return out
        if not out['robots_allowed']:
            out['status']='robots_disallowed';return out
        code,url,body,truncated=get(s['url']); page=Page();page.feed(body)
        text=' '.join(page.text)
        links=sorted(set(urljoin(url,x) for x in page.links if any(k in x.lower() for k in ('event','whats-on','whatson','activit','children','family','story','rhyme'))))
        out.update(status='readable_pending_validation' if len(text)>200 else 'insufficient_content',http_status=code,final_url=url,text_chars=len(text),truncated=truncated,detail_candidates=links[:12],excerpt=text[:700])
    except urllib.error.HTTPError as e: out.update(status='http_failed',http_status=e.code,error=str(e))
    except Exception as e: out.update(status='access_failed',error=str(e)[:300])
    finally: out['elapsed_seconds']=round(time.monotonic()-start,2)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--registry',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    sources=[s for s in json.loads(Path(args.registry).read_text(encoding='utf-8')) if s['category']!='venue_reference']
    results=[]
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(audit,sources):
            results.append(row)
            Path(args.output).write_text(json.dumps({'ai_calls':0,'database_writes':0,'max_workers':4,'max_bytes_per_response':MAX_BYTES,'sources':results},indent=2),encoding='utf-8')
            print(row['name'],row['status'],flush=True)
    assert len(results)==len(sources)

if __name__=='__main__':main()

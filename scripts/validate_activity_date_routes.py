"""Bounded read-only provider date checks; not source activation/full discovery."""
import datetime as dt
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import requests
from activity_dates import published_date_fields
from classforkids_calendar import parse_detail
import worker

TARGETS=[('Saturdads',"https://haysouthcambs.co.uk/activities/saturdads-at-st-johns-church-waterbeach/","Saturdads at St John's Church Waterbeach"),('Hoop Little Forts','https://hoop.co.uk/e/CdAXHY/','Little Forts Playgroup'),('ClassForKids Mini Movers','https://little-movers-gym.classforkids.io/info/123','Mini Movers Gymnastics')]

def main():
    today=dt.datetime.now(dt.timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('Europe/London')).date()
    results=[]
    for name,url,title in TARGETS:
        for number in (1,2):
            result=dict(name=name,url=url,pass_number=number,checked_at=dt.datetime.now(dt.timezone.utc).isoformat())
            try:
                allowed,reason=worker.robots_allows(url)
                if not allowed:raise ValueError('Robots blocked: '+reason)
                response=requests.get(url,headers={'User-Agent':'Mozilla/5.0 (compatible; DadspaceEventsBot/1.0)'},timeout=(5,20))
                response.raise_for_status();response.encoding='utf-8'
                if response.url.rstrip('/')!=url.rstrip('/'):raise ValueError('Redirect requires review')
                fields=parse_detail(response.text,url,today) if 'classforkids' in url else published_date_fields(response.text,url,title)
                result.update(status='ok',fields=fields)
            except Exception as exc:result.update(status='failed',reason=str(exc))
            results.append(result);print(name,number,result['status'],flush=True)
    destination=Path('activity-date-review');destination.mkdir(exist_ok=True)
    (destination/'results.json').write_text(json.dumps(dict(gemini_calls=0,database_writes=0,note='Date/detail parser route checks, not full source discovery or activation. Two passes are not seven-day scheduling evidence.',results=results),indent=2),encoding='utf-8')
    for name,_,_ in TARGETS:
        pair=[r for r in results if r['name']==name]
        if any(r['status']!='ok' for r in pair) or pair[0].get('fields')!=pair[1].get('fields'):raise SystemExit('Failed or changing route: '+name)

if __name__=='__main__':main()

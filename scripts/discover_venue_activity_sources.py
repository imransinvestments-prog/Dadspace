"""Discover listing links from the complete canonical museum website inventory.

Process bounded batches of distinct domains; preserve venue IDs and actual links.
Never guess /events URLs, create venues, call AI or activate database sources.
The inventory is supplied from the read-only evidence export.
"""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import worker as base
from activity_source_discovery import detail_urls


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--inventory',required=True)
    parser.add_argument('--offset',type=int,default=0)
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    inventory=json.loads(Path(args.inventory).read_text(encoding='utf-8'))
    groups=[g for g in inventory if g['domain']!='NO_WEBSITE']
    offset=max(0,args.offset); limit=min(40,max(1,args.limit))
    results=[]
    for group in groups[offset:offset+limit]:
        venues=group['venues']
        row={'domain':group['domain'],'venue_ids':[v['id'] for v in venues],
             'venue_count':len(venues),'status':'pending_extraction'}
        url=next(v['website'] for v in venues if v.get('website'))
        row['inventory_url']=url
        try:
            allowed,reason=base.robots_allows(url)
            if not allowed:
                row.update(status='blocked_robots',error=reason)
            else:
                html=base.fetch_html_requests(url)
                row['candidate_listing_urls']=detail_urls(html,url,4)
                if base.soft_404_title([(url,html)]):
                    row['status']='soft_404'
                elif not row['candidate_listing_urls']:
                    row['status']='no_listing_links_found'
        except Exception as exc:
            row.update(status='access_failed',error=str(exc)[:500])
        results.append(row)
        time.sleep(base.PAUSE_SECONDS)
        output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps({'ai_calls':0,'database_writes':0,'offset':offset,
            'next_offset':offset+len(results),'total_domains':len(groups),'sources':results},indent=2),encoding='utf-8')
        print(row['domain'],row['status'],len(row.get('candidate_listing_urls',[])),flush=True)


if __name__=='__main__':
    main()

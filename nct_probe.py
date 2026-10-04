import json,re,requests
from bs4 import BeautifulSoup
u='https://www.nct.org.uk/local-activities-meet-ups/watford'
r=requests.get(u,timeout=30,headers={'User-Agent':'Mozilla/5.0 (compatible; DadspaceNCTBot/1.0)'})
print('status',r.status_code,'chars',len(r.text),'url',r.url)
s=BeautifulSoup(r.text,'html.parser')
needle='NCT Watford Walk & Talk - Rickmansworth Aquadrome'
node=s.find(string=lambda x: x and needle.lower() in x.lower())
print('found',bool(node))
if node:
    cur=node.parent
    for i in range(8):
        if cur is None: break
        print('\nLEVEL',i,'TAG',cur.name,'CLASS',cur.get('class'),'ID',cur.get('id'))
        print(str(cur)[:4000])
        cur=cur.parent
print('\nJSONLD')
for tag in s.find_all('script',type='application/ld+json'):
    txt=tag.string or tag.get_text()
    if 'Event' in txt or 'event' in txt: print(txt[:5000])
print('\nSITEMAPS')
rr=requests.get('https://www.nct.org.uk/robots.txt',timeout=30,headers={'User-Agent':'Mozilla/5.0'})
print(rr.status_code,rr.text[-3000:])
print('probe complete')

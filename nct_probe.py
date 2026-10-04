import re,requests,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
H={'User-Agent':'Mozilla/5.0 (compatible; DadspaceNCTBot/1.0)'}
for u in ['https://www.nct.org.uk/sitemap.xml','https://www.nct.org.uk/sitemap_index.xml','https://www.nct.org.uk/sitemap/sitemap.xml','https://www.nct.org.uk/sitemap.xml.gz']:
    try:
        r=requests.get(u,timeout=30,headers=H)
        print('SITEMAP',u,r.status_code,r.headers.get('content-type'),len(r.content),r.url)
        text=r.text[:500000] if 'gzip' not in (r.headers.get('content-type') or '') else ''
        urls=re.findall(r'<loc>(.*?)</loc>',text,re.I)
        print('URLS',len(urls),'NCT_LOCAL',sum('/local-activities-meet-ups/' in x for x in urls))
        print('\n'.join([x for x in urls if '/local-activities-meet-ups/' in x][:20]))
    except Exception as e: print('ERR',u,type(e).__name__,e)
main=requests.get('https://www.nct.org.uk/local-activities-meet-ups',timeout=30,headers=H)
s=BeautifulSoup(main.text,'html.parser')
links=sorted({a.get('href') for a in s.find_all('a',href=True) if '/local-activities-meet-ups/' in a.get('href','')})
print('MAIN LOCAL LINKS',len(links)); print('\n'.join(links[:50]))
print('FORM ACTIONS',[(f.get('action'),f.get('method'),[i.get('name') for i in f.find_all(['input','select'])]) for f in s.find_all('form')][:20])
for scr in s.find_all('script'):
    t=scr.string or scr.get_text() or ''
    if 'postcode' in t.lower() and ('branch' in t.lower() or 'event' in t.lower()):
        print('SCRIPT',t[:8000])
print('probe discovery complete')

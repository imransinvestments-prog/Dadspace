"""Build a local review worksheet from a frozen, source-balanced DB sample."""
import csv
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'artefacts/data/ds10-human-review-2026-10-11.json'
OUTPUT=ROOT/'artefacts/documentation/ds10-human-review-2026-10-11.html'

def main():
    sample=json.loads(SOURCE.read_text(encoding='utf-8'))
    rows=sample['rows']
    fields=['id','title','category','age_range','schedule_text','start_date','end_date','time_text',
            'location','event_url','last_seen_at','last_verified_at','relevant','current','actionable','notes']
    with SOURCE.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
    cards=[]
    for i,row in enumerate(rows):
        def esc(key): return html.escape(str(row.get(key) or 'Missing'))
        details=''.join('<dt>'+label+'</dt><dd>'+esc(key)+'</dd>' for key,label in [
            ('category','Category'),('age_range','Ages'),('schedule_text','Schedule'),
            ('time_text','Time'),('start_date','First date'),('end_date','Last date'),
            ('location','Location'),('cost_text','Cost'),('last_seen_at','Last seen'),
            ('last_verified_at','Last verified'),('venue_id','Canonical venue')])
        url=row.get('event_url') or ''
        link=('<a target="_blank" rel="noopener noreferrer" href="'+html.escape(url,quote=True)+'">Open official detail</a>') if url.startswith('https://') else 'Missing HTTPS detail link'
        controls=''.join('<label>'+label+' <select data-field="'+key+'"><option value="">Unreviewed</option><option value="yes">Yes</option><option value="no">No</option></select></label>' for key,label in [('relevant','Relevant to families'),('current','Current opportunity'),('actionable','Actionable location / dates / booking')])
        cards.append('<article data-id="'+row['id']+'"><h2>'+str(i+1)+'. '+esc('title')+'</h2><p>'+link+'</p><dl>'+details+'</dl><details><summary>Stored description and provenance</summary><p>'+esc('description')+'</p><p>'+esc('source_url')+'</p></details><div class="controls">'+controls+'</div><label>Notes / corrections <textarea data-field="notes"></textarea></label></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dadspace — 100 activity review</title>
<style>body{font:16px system-ui;color:#17243b;background:#f3f6fa;max-width:1000px;margin:auto;padding:24px}header{position:sticky;top:0;background:#fff;padding:16px;border-bottom:3px solid #396a62;z-index:1}article{background:#fff;margin:22px 0;padding:24px;border-radius:12px}h1{font-size:24px;margin:0 0 8px}h2{font-size:20px}dl{display:grid;grid-template-columns:160px 1fr;gap:8px}dt{font-weight:600}dd{margin:0;overflow-wrap:anywhere}.controls{display:flex;gap:16px;flex-wrap:wrap;margin:18px 0}select,button,textarea{font:inherit;padding:8px}label{display:block}textarea{display:block;width:95%;min-height:60px}button{cursor:pointer}a{color:#175d83}#summary{font-weight:650}@media(max-width:600px){dl{grid-template-columns:1fr}dd{margin-bottom:10px}}</style>
<header><h1>Dadspace: 100 activity review</h1><p>Reviewer: Imran Tajuddin. Frozen 11 October 2026 sample across 20 sources; includes incomplete and stale rows. Check the official detail before answering. Stored evidence is not a currentness guarantee.</p><p id="summary"></p><button id="export">Download review results</button> <label><input id="pending" type="checkbox"> Show unreviewed only</label></header>
<p>Mark all three questions for every item. A row passes only when all three are Yes. Closure requires all 100 reviewed and at least 90 passes. Pilot breadth and scheduled source reliability are separate checks. Responses stay in this browser; downloading does not publish or change Dadspace.</p>
'''+''.join(cards)+'''
<script>
const key='dadspace-ds10-review-2026-10-11';let answers={};try{answers=JSON.parse(localStorage.getItem(key)||'{}')}catch(e){}
const articles=[...document.querySelectorAll('article')];
function update(){let reviewed=0,passed=0;for(const a of articles){const r=answers[a.dataset.id]||{};const done=['relevant','current','actionable'].every(k=>['yes','no'].includes(r[k]));if(done)reviewed++;if(done&&['relevant','current','actionable'].every(k=>r[k]==='yes'))passed++;a.hidden=document.querySelector('#pending').checked&&done}document.querySelector('#summary').textContent=reviewed+'/100 reviewed • '+passed+'/100 pass • '+(reviewed===100?(passed>=90?'Quality target met; other acceptance checks remain':'Quality target not met'):'Awaiting completed human review');try{localStorage.setItem(key,JSON.stringify(answers))}catch(e){}}
for(const a of articles){for(const c of a.querySelectorAll('[data-field]')){c.value=(answers[a.dataset.id]||{})[c.dataset.field]||'';c.addEventListener('input',()=>{answers[a.dataset.id]??={};answers[a.dataset.id][c.dataset.field]=c.value;update()})}}
document.querySelector('#pending').addEventListener('change',update);
document.querySelector('#export').addEventListener('click',()=>{const result={sample:'ds10-human-review-2026-10-11.json',reviewer:'Imran Tajuddin',reviewed_at:new Date().toISOString(),answers};const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='ds10-human-review-results.json';a.click();URL.revokeObjectURL(url)});update();
</script></html>'''
    OUTPUT.write_text(page,encoding='utf-8')
    print('Built',len(rows),'review cards:',OUTPUT)

if __name__=='__main__': main()

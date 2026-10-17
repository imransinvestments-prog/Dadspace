"""Build a frozen correction preview and guarded SQL. Default SQL rolls back."""
from __future__ import annotations
from collections import Counter
import csv
import html
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from venue_country import normalize_postcode, resolve_country

DATA = ROOT / 'artefacts/data'
STEM = 'places-data-review-2026-10-17'
NURSERY = '4437eb40-96da-4548-935f-a0a22c9ad7ff'

def make_plan(cohort, lookup, source_rows):
    sources = {r['id']: r for r in source_rows}
    changes = []
    for row in cohort['libraries']:
        source = sources.get(row['id'], {})
        evidence = resolve_country(row.get('postcode'), lookup['results'].get(normalize_postcode(row.get('postcode'))), source.get('authority_code'))
        evidence['checked_at'] = lookup['retrieved_at']
        evidence['retained_source_id'] = source.get('provenance_id')
        evidence['authority_code'] = source.get('authority_code')
        changes.append({'id': row['id'], 'name': row['venue_name'], 'postcode': row.get('postcode'),
                        'fingerprint': row['fingerprint'], 'kind': 'library',
                        'country': evidence['country'], 'evidence': evidence})
    nursery = cohort['nursery']
    changes.append({'id': NURSERY, 'name': nursery['venue_name'], 'postcode': nursery['postcode'],
        'fingerprint': cohort['nursery_fingerprint'], 'kind': 'nursery', 'country': nursery['country'],
        'evidence': {'owner_confirmation': '2026-10-16: actual nursery, not a playground',
                     'source_url': nursery['source_url'],
                     'corroboration': 'https://reports.ofsted.gov.uk/provider/16/2516013',
                     'address_caveat': 'Imported address is approximate; no address correction proposed.',
                     'access': None, 'category': 'nursery', 'public_visible': False}})
    counts = Counter(c['country'] or 'Unknown' for c in changes if c['kind'] == 'library')
    return {'sprint': 171, 'tickets': [162, 100], 'frozen_at': lookup['retrieved_at'],
            'library_count': len(cohort['libraries']), 'nation_totals': dict(counts), 'changes': changes}

def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"

def build_sql(plan, commit=False):
    changes = plan['changes']
    if len({r['id'] for r in changes}) != len(changes):
        raise ValueError('Duplicate IDs')
    if sum(r['kind'] == 'nursery' and r['id'] == NURSERY for r in changes) != 1:
        raise ValueError('Expected the single approved nursery identity')
    if sum(r['kind'] == 'library' for r in changes) != plan['library_count']:
        raise ValueError('Library denominator mismatch')
    import re
    for r in changes:
        if not re.fullmatch(r'[0-9a-f-]{36}', r['id']) or not re.fullmatch(r'[0-9a-f]{32}', r['fingerprint']):
            raise ValueError('Invalid ID/fingerprint')
        if r['kind'] not in ('nursery', 'library') or r['country'] not in (None, 'England', 'Wales', 'Scotland', 'Northern Ireland'):
            raise ValueError('Unapproved change')
        if r['kind'] == 'library' and r['country'] != r['evidence']['country']:
            raise ValueError('Country differs from evidence')
    raw = sql_literal(json.dumps(changes, ensure_ascii=True))
    ending = 'commit;' if commit else 'rollback; -- Review only: no persistent changes'
    return f"""-- #171 / #162 / #100. Apply protection migration first. Owner data approval required.
begin;
set local lock_timeout = '5s';
set local statement_timeout = '120s';
set local standard_conforming_strings = on;
create temporary table places_plan on commit drop as
select * from jsonb_to_recordset({raw}::jsonb)
as x(id uuid, name text, postcode text, fingerprint text, kind text, country text, evidence jsonb);
alter table places_plan add primary key(id);
do $$
begin
  if not exists(select 1 from pg_trigger where tgname='venues_preserve_reviewed_geography' and tgrelid='public.venues'::regclass) then
    raise exception 'Missing reviewed-field protection migration';
  end if;
  perform 1 from public.venues v join places_plan p on p.id=v.id order by v.id for update of v;
  if (select count(*) from public.venues where category='library' and public_visible=true) <> {plan['library_count']}
     or exists(select 1 from public.venues v where category='library' and public_visible=true and not exists(select 1 from places_plan p where p.id=v.id and p.kind='library')) then
    raise exception 'Library cohort changed: rebuild/review plan';
  end if;
  if exists(select 1 from places_plan p left join public.venues v on v.id=p.id where v.id is null or md5(to_jsonb(v)::text)<>p.fingerprint) then
    raise exception 'Concurrent change/missing row: rebuild/review plan';
  end if;
  if exists(select 1 from public.venue_sources s join places_plan p on p.id=s.venue_id
      where s.source_name in ('Dadspace reviewed geography','Dadspace reviewed classification')) then
    raise exception 'Existing correction audit: inspect rather than overwrite';
  end if;
end $$;
create temporary table places_before on commit drop as
select v.id,to_jsonb(v) as before_row from public.venues v join places_plan p on p.id=v.id;
select set_config('dadspace.review_write','on',true);
update public.venues v set country=p.country from places_plan p where v.id=p.id and p.kind='library';
update public.venues v set category='nursery', public_visible=false,
  review_reason=concat_ws(E'\\n',nullif(v.review_reason,''),
  '2026-10-17 #162 owner-confirmed nursery, not a playground. Earlier playground-access confirmation is superseded for this misclassified record. Access remains unknown; publication held until visitor suitability is evidenced.'),
  ops_reviewed_at=now()
from places_plan p where v.id=p.id and p.kind='nursery';
do $$
begin
  if exists(select 1 from public.venues v join places_before b on b.id=v.id join places_plan p on p.id=v.id
     where (to_jsonb(v) - case when p.kind='library' then array['country'] else array['category','public_visible','review_reason','ops_reviewed_at'] end)
        is distinct from (b.before_row - case when p.kind='library' then array['country'] else array['category','public_visible','review_reason','ops_reviewed_at'] end)) then
    raise exception 'Unapproved field changed';
  end if;
  if exists(select 1 from public.venues v join places_plan p on p.id=v.id where p.kind='library' and v.country is distinct from p.country)
     or exists(select 1 from public.venues where id='{NURSERY}' and (category<>'nursery' or public_visible or access is not null)) then
    raise exception 'Correction readback failed';
  end if;
end $$;
insert into public.venue_sources(venue_id,source_name,source_record_id,source_url,source_role,match_method,match_confidence,source_payload,last_seen_at,updated_at)
select v.id,case when p.kind='library' then 'Dadspace reviewed geography' else 'Dadspace reviewed classification' end,
 v.id::text,p.evidence->>'source_url','venue_reference','reviewed_exact_identity',1,
 p.evidence || jsonb_build_object('ticket',case when p.kind='library' then 100 else 162 end,
 'accepted',true,'country',p.country,'before_row',b.before_row,'after_fingerprint',md5(to_jsonb(v)::text)),now(),now()
from public.venues v join places_plan p on p.id=v.id join places_before b on b.id=v.id;
select coalesce(v.country,'Unknown') as nation,count(*) from public.venues v join places_plan p on p.id=v.id where p.kind='library' group by v.country order by nation;
{ending}
"""

ROLLBACK = """-- Exact reviewed correction rollback; aborts if any target row has since changed.
-- Owner rollback approval required. Default is inspection/rollback, not commit.
begin;
set local lock_timeout='5s';
create temporary table places_undo on commit drop as
select s.id as audit_id,s.venue_id,s.source_payload from public.venue_sources s
where s.source_name in ('Dadspace reviewed geography','Dadspace reviewed classification')
and s.source_payload->>'ticket' in ('100','162');
do $$ begin
 perform 1 from public.venues v join places_undo u on u.venue_id=v.id order by v.id for update of v;
 if not exists(select 1 from places_undo) or exists(select 1 from places_undo u left join public.venues v on v.id=u.venue_id
    where v.id is null or md5(to_jsonb(v)::text)<>u.source_payload->>'after_fingerprint') then
   raise exception 'Rollback target missing or changed: inspect before recovery';
 end if;
end $$;
select set_config('dadspace.review_write','on',true);
update public.venues v set country=u.source_payload->'before_row'->>'country',
category=u.source_payload->'before_row'->>'category',
public_visible=(u.source_payload->'before_row'->>'public_visible')::boolean,
review_reason=u.source_payload->'before_row'->>'review_reason',
ops_reviewed_at=(u.source_payload->'before_row'->>'ops_reviewed_at')::timestamptz
from places_undo u where v.id=u.venue_id;
-- Retain the audit before-image. Mark acceptance false so the protection releases country.
update public.venue_sources s set source_payload=s.source_payload || jsonb_build_object('accepted',false,'rolled_back_at',now()),updated_at=now()
from places_undo u where s.id=u.audit_id;
rollback;
"""

def main():
    cohort=json.loads((DATA/'places-data-cohort-2026-10-17.json').read_text(encoding='utf-8'))
    lookup=json.loads((DATA/'library-postcode-evidence-2026-10-17.json').read_text(encoding='utf-8'))
    sources=json.loads((DATA/'library-source-geography-2026-10-17.json').read_text(encoding='utf-8'))['rows']
    plan=make_plan(cohort,lookup,sources)
    (DATA/f'{STEM}.json').write_text(json.dumps(plan,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    (DATA/f'{STEM}.sql').write_text(build_sql(plan),encoding='utf-8')
    (DATA/f'{STEM}-rollback.sql').write_text(ROLLBACK,encoding='utf-8')
    fields=['id','name','postcode','before_country','proposed_country','reason']
    output=io.StringIO(); writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader()
    for r in plan['changes']:
        if r['kind']=='library':writer.writerow(dict(id=r['id'],name=r['name'],postcode=r['postcode'],before_country='',proposed_country=r['country'] or 'Unknown',reason=r['evidence']['reason']))
    (DATA/f'{STEM}.csv').write_text(output.getvalue(),encoding='utf-8')
    unknown=[r for r in plan['changes'] if r['kind']=='library' and not r['country']]
    rows=''.join('<tr>'+''.join(f'<td>{html.escape(str(v or ""))}</td>' for v in (r['name'],r['postcode'],r['evidence']['reason']))+'</tr>' for r in unknown)
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Sprint 3 correction review</title><style>body{{font:18px system-ui;max-width:1000px;margin:32px auto;padding:16px;background:#f6f7fa;color:#16213a}}section{{background:white;padding:24px;border-radius:16px;margin:20px 0}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #ddd}}table{{width:100%}}strong{{color:#994000}}</style><h1>Sprint 3 · Places data accuracy</h1><p>Prepared 17 October 2026 · <strong>Proposal only — live data unchanged</strong></p><section><h2>One nursery correction</h2><p>The Little Garden Nursery · W3 7LH</p><p>Children’s playground → <b>Nursery</b><br>Publication: on → <b>off</b><br>Access: unknown → <b>unknown</b></p><p>Owner confirmation corroborated by Ofsted nursery identity. Approximate imported address stays unchanged. Earlier playground-public-access confirmation is superseded for this row.</p></section><section><h2>{plan['library_count']:,} libraries reconciled</h2><p>{html.escape(str(plan['nation_totals']))}</p><p>Exact postcode and GSS district-code agreement required; authority conflicts stay unknown. All library publication flags stay on. Four UK-nation examples passed.</p><h3>{len(unknown)} records remain unknown</h3><table><tr><th>Library</th><th>Postcode</th><th>Reason</th></tr>{rows}</table></section><section><h2>Review and recovery</h2><p>Country changes only for libraries; no hours, fees, location or access changes. Each row retains source evidence and a before-image. Scripts check cohort membership and fingerprints, refuse stale rows, default to rollback and include a guarded recovery script.</p><p>Suggested approval: accept the nursery hold, the evidenced nation corrections, and leaving these unmatched records unknown. No need to manually review all 3,440 rows.</p></section></html>'''
    target=ROOT/'artefacts/documentation/places-data-review-2026-10-17.html';target.write_text(page,encoding='utf-8')
    print(json.dumps({'library_count':plan['library_count'],'nation_totals':plan['nation_totals'],'unknown':len(unknown)},indent=2))

if __name__=='__main__':main()

"""Real multi-connection PostgreSQL gate, exclusively on a disposable CI service."""
import concurrent.futures
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
SOURCE='10000000-0000-0000-0000-000000000001'

def psql(sql, *, app='provider-observer', check=True):
    env={**os.environ,'PGAPPNAME':app}
    return subprocess.run(['psql','-X','-qAt','-v','ON_ERROR_STOP=1'],input=sql,text=True,
                          capture_output=True,env=env,check=check)

def write_sql(row):
    keys=list(row)
    if any(not re.fullmatch('[a-z_]+',k) for k in keys): raise ValueError('Invalid fixture column')
    facts=json.dumps(row).replace("'","''")
    return f"insert into collected_events({','.join(keys)}) select {','.join(keys)} from jsonb_populate_record(null::collected_events,'{facts}'::jsonb) on conflict(dedupe_key) do update set "+','.join(f'{k}=excluded.{k}' for k in keys)+' returning id;'

def observe(app, predicate):
    return psql(f"select pid from pg_stat_activity where application_name='{app}' and {predicate};").stdout.strip()

def main():
    if os.getenv('IDENTITY_TEST_DATABASE')!='disposable' or os.getenv('PGHOST')!='localhost':
        raise RuntimeError('This gate requires the disposable localhost CI database')
    os.chdir(ROOT)
    for file in ['tests/operations-review-fixture.sql','tests/provider-session-bootstrap.sql',
                 'supabase/migrations/20261002_stable_event_identity_trigger.sql',
                 'scripts/operations-review.sql','supabase/migrations/20261017102447_operations_review_edit_reject.sql']:
        psql(Path(file).read_text(encoding='utf-8'))
    raw=Path('supabase/migrations/20261012121658_ds10_reversible_listing_withdrawal.sql').read_text(encoding='utf-8')
    psql(raw[raw.index('CREATE OR REPLACE FUNCTION public.dadspace_set_event_identity()'):])
    psql(f"insert into sources values('{SOURCE}','library_portal_sessions_v1');")
    psql(Path('supabase/migrations/20261018213916_reviewed_provider_session_identity.sql').read_text(encoding='utf-8'))
    for file in ['tests/operations-review-transactions.sql','tests/operations-review-edit-transactions.sql']:
        psql(Path(file).read_text(encoding='utf-8'))
    psql(f"insert into activity_identity_sources values('{SOURCE}','ealing.events.mylibrary.digital',array['264038','319285'],'Disposable approved-policy fixture',now());")
    rows=json.loads(Path('tests/fixtures/provider-session-worker-rows.json').read_text(encoding='utf-8'))
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for same in (True,False):
            psql('truncate collected_events,activity_identity_audit;')
            first=pool.submit(psql,'begin; '+write_sql(rows[0])+' select pg_sleep(3); commit;',app='provider-first')
            first_pid=''
            for _ in range(30):
                first_pid=observe('provider-first',"wait_event='PgSleep'")
                if first_pid: break
                time.sleep(.05)
            assert first_pid,'First connection did not hold its write transaction'
            second=pool.submit(psql,'begin; '+write_sql(rows[0] if same else rows[1])+' commit;',app='provider-second')
            lock_pid=''
            if same:
                for _ in range(30):
                    lock_pid=observe('provider-second',"wait_event_type='Lock'")
                    if lock_pid:break
                    time.sleep(.05)
                assert lock_pid and lock_pid!=first_pid,'Independent session lock was not observed'
            first.result(timeout=15);second.result(timeout=15)
            actual=int(psql('select count(*) from collected_events;').stdout.strip())
            assert actual==(1 if same else 2)
            assert int(psql('select count(*) from activity_identity_audit;').stdout.strip())>=2
            results.append({'case':'concurrent_same_session' if same else 'concurrent_distinct_sessions',
                            'rows':actual,'independent_lock_observed':bool(lock_pid),'passed':True})
    inverse=Path('scripts/rollback-provider-session-identity.sql').read_text(encoding='utf-8')
    blocked=psql(inverse,check=False)
    assert blocked.returncode!=0 and 'Stale or nonempty' in blocked.stderr
    assert int(psql('select count(*) from collected_events;').stdout.strip())==2
    results.append({'case':'nonempty_inverse_preserves_rows','passed':True})
    # Reset disposable synthetic records only, then verify the empty-release inverse.
    psql('truncate collected_events,activity_identity_audit; delete from activity_identity_sources;')
    psql(inverse)
    assert psql("select to_regclass('activity_identity_sources') is null;").stdout.strip()=='t'
    results.append({'case':'empty_release_inverse','passed':True})
    output=ROOT/'review/provider-identity-gates';output.mkdir(parents=True,exist_ok=True)
    (output/'postgres.json').write_text(json.dumps({'engine':psql('select version();').stdout.strip(),
        'production_connections':0,'cases':results},indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results))

if __name__=='__main__':main()

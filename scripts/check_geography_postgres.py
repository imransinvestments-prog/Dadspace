"""Real PostgreSQL gate, restricted to the workflow's disposable local database."""
import os
from pathlib import Path
import subprocess
import sys

from geography_catalogue import emit_seed
import io
import json

ROOT=Path(__file__).resolve().parents[1]


def query(sql,expected=True):
    result=subprocess.run(['psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],input=sql,
                          text=True,capture_output=True,timeout=60,check=False)
    if (result.returncode==0)!=expected:
        raise RuntimeError('Unexpected disposable SQL result: '+result.stderr[-1200:])
    return result.stdout.strip()


def main():
    if os.environ.get('GEOGRAPHY_TEST_DATABASE')!='disposable' or os.environ.get('PGHOST') not in ('localhost','127.0.0.1') or os.environ.get('PGDATABASE')!='geography_test':
        raise SystemExit('Only the explicit disposable local geography_test database is allowed')
    query('create role anon;create role authenticated;create role service_role;')
    query((ROOT/'supabase/migrations/20261018224639_uk_geography_reference.sql').read_text())
    reference=json.loads((ROOT/'geography/reference.json').read_text(encoding='utf-8'))
    stream=io.StringIO();emit_seed(reference,stream);seed=stream.getvalue()
    query(seed);query(seed)
    assert query('select count(*) from geography_postcodes')=='28'
    query('set role anon;select * from geography_postcodes;',expected=False)
    query('set role authenticated;select * from geography_areas;',expected=False)
    assert query('set role service_role;select count(*) from geography_postcodes;')=='28'
    query('set role service_role;delete from geography_postcodes;',expected=False)
    query("update geography_areas set name='invalid';",expected=False)
    query((ROOT/'scripts/rollback-geography-empty.sql').read_text(),expected=False)
    assert query('select count(*) from geography_postcodes')=='28'
    print(json.dumps(dict(database='PostgreSQL',postcodes=28,repeat_import='passed',
                          public_access='denied',service_writes='denied',history_inverse='refused',passed=True)))


if __name__=='__main__':main()

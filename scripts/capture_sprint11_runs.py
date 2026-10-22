"""Read public scheduled-run metadata; no dispatch, retry or production write."""
import datetime as dt
import json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
API='https://api.github.com/repos/imransinvestments-prog/Dadspace'


def main():
    output={}
    for workflow in ('daily-workers.yml','original-content.yml'):
        response=requests.get(API+'/actions/workflows/'+workflow+'/runs',
            params={'event':'schedule','branch':'main','per_page':100},timeout=25)
        response.raise_for_status();payload=response.json()
        if payload.get('total_count',0)>100: output[workflow+'_older_omitted']=True
        output[workflow]=[{key:row.get(key) for key in ('id','event','status','conclusion','created_at','updated_at','head_sha','html_url','run_attempt')}
                          for row in payload['workflow_runs']]
    body=dict(captured_at=dt.datetime.now(dt.timezone.utc).isoformat(),source=API,
              database_writes=0,dispatches=0,workflows=output)
    (ROOT/'artefacts/data/sprint11-scheduled-runs.json').write_text(json.dumps(body,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:len(value) for key,value in output.items() if isinstance(value,list)}))


if __name__=='__main__':main()

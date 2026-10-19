"""Expected London slots, with attribution only from explicitly reviewed retained evidence."""
import datetime as dt
import hashlib,json,subprocess
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
ZONE=ZoneInfo('Europe/London')
STABLE=dt.datetime(2026,10,17,20,33,40,tzinfo=dt.timezone.utc)
HOURS={'daily-workers.yml':(7,19),'original-content.yml':(7,9)}
START=dt.date(2026,10,18)

def timestamp(value):
 result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
 if result.tzinfo is None:raise ValueError('Timestamp must include timezone')
 return result.astimezone(dt.timezone.utc)

def expected_slots(day,hours):
 return [dt.datetime.combine(day,dt.time(hour,17),ZONE).astimezone(dt.timezone.utc) for hour in hours]

def config_hash(sha,workflow):
 try:return hashlib.sha256(subprocess.check_output(['git','show',f'{sha}:.github/workflows/{workflow}'],cwd=ROOT)).hexdigest()
 except subprocess.CalledProcessError:return None

def reviewed_assignments(evidence,raw,slots,cutoff):
 """Reject the complete input on malformed, conflicting or reused evidence; never partially trust it."""
 if not isinstance(evidence,dict) or evidence.get('version')!=1 or not isinstance(evidence.get('assignments'),list):raise ValueError('Invalid slot evidence envelope')
 result={};used_runs=set();used_urls=set()
 for item in evidence['assignments']:
  workflow=item['workflow'];slot=timestamp(item['expected_at']);key=(workflow,slot)
  run_key=(workflow,str(item['run_id']))
  url=item['evidence_url'];parsed=urlsplit(url)
  if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:raise ValueError('Retained HTTPS evidence URL required')
  if not isinstance(item['reviewed_by'],str) or not item['reviewed_by'].strip() or timestamp(item['reviewed_at'])>cutoff:raise ValueError('Dated reviewer required')
  if key not in slots or slot>cutoff or key in result or run_key in used_runs or url in used_urls:raise ValueError('Conflicting, future or reused slot evidence')
  matches=[r for r in raw['workflows'].get(workflow,[]) if str(r['id'])==str(item['run_id']) and r.get('run_attempt')==item['run_attempt'] and r['head_sha']==item['head_sha']]
  if len(matches)!=1 or matches[0].get('event')!='schedule':raise ValueError('Evidence must bind one captured scheduled run/attempt/SHA')
  if timestamp(matches[0]['created_at'])<slot or timestamp(item['reviewed_at'])<timestamp(matches[0]['created_at']):raise ValueError('Evidence predates slot or run')
  result[key]=item;used_runs.add(run_key);used_urls.add(url)
 return result

def build_ledger(raw,evidence=None,hash_fn=config_hash,start=START):
 cutoff=timestamp(raw['captured_at'])
 # Seven complete London dates, including the clock change when the chosen window crosses it.
 slots={(workflow,slot) for workflow,hours in HOURS.items() for offset in range(7) for slot in expected_slots(start+dt.timedelta(days=offset),hours)}
 assignments=reviewed_assignments(evidence,raw,slots,cutoff) if evidence is not None else {}
 output={'captured_at':raw['captured_at'],'timezone':'Europe/London','stable_release':'31b8c1f','stable_at':STABLE.isoformat(),'window':f'Seven London days from {start.isoformat()}; older evidence retained separately.','warnings':{'dispatch_minutes':60,'completion_hours':4,'source_check_hours':36},'workflows':[]}
 for workflow,hours in HOURS.items():
  stable_hash=hash_fn('31b8c1f',workflow);runs=[];by_identity={}
  for row in raw['workflows'].get(workflow,[]):
   created=timestamp(row['created_at'])
   if created<STABLE:continue
   candidates=[slot for slot in expected_slots(created.astimezone(ZONE).date(),hours) if slot<=created]
   eligible=stable_hash is not None and hash_fn(row['head_sha'],workflow)==stable_hash
   delay=(created-max(candidates)).total_seconds()/60 if candidates else None
   run={**row,'configuration_matches_stable':eligible,'candidate_expected_at':[x.isoformat() for x in candidates],'slot_assignment':'unknown_no_triggering_cron_identity','minimum_same_day_delay_minutes':round(delay,2) if delay is not None else None,'late_even_against_latest_candidate':delay>60 if delay is not None else None,'completion_elapsed_minutes':round((timestamp(row['updated_at'])-created).total_seconds()/60,2)}
   runs.append(run);by_identity[(str(row['id']),row.get('run_attempt'))]=run
  expected=[]
  for _,slot in sorted(k for k in slots if k[0]==workflow):
   entry={'expected_at':slot.isoformat(),'london':slot.astimezone(ZONE).isoformat(),'state':'elapsed_unattributed' if slot<=cutoff else 'future_not_due'}
   proof=assignments.get((workflow,slot))
   if proof:
    run=by_identity.get((str(proof['run_id']),proof['run_attempt']))
    if run is None:raise ValueError('Evidence run predates stable release')
    created=timestamp(run['created_at']);finished=timestamp(run['updated_at'])
    dispatch=(created-slot).total_seconds()/60;completion=(finished-slot).total_seconds()/60
    if finished<created or finished>cutoff:raise ValueError('Invalid captured completion timestamp')
    success=run['status']=='completed' and run['conclusion']=='success'
    state='configuration_mismatch' if not run['configuration_matches_stable'] else 'failed' if run['status']=='completed' and not success else 'incomplete' if not success else 'late' if dispatch>60 or completion>240 else 'success'
    entry.update(state=state,run_id=run['id'],run_attempt=run['run_attempt'],head_sha=run['head_sha'],evidence_url=proof['evidence_url'],reviewed_by=proof['reviewed_by'],reviewed_at=proof['reviewed_at'],dispatch_minutes=round(dispatch,2),completion_from_slot_minutes=round(completion,2),dispatch_warning=dispatch>60,completion_warning=completion>240,completion_timestamp_basis='captured_run_updated_at_conservative_upper_bound')
    run['slot_assignment']='reviewed_retained_evidence';run['assigned_expected_at']=slot.isoformat()
   expected.append(entry)
  covered=all(s['state']=='success' for s in expected)
  output['workflows'].append({'workflow':workflow,'stable_config_sha256':stable_hash,'expected_slots':expected,'observed_runs':runs,'slot_coverage':'met' if covered else 'not_met','acceptance':'not_met','reason':'Slot coverage alone does not establish per-feed source, publication, freshness, Friday or recovery acceptance.','feed_publication_acceptance':'not_evaluated'})
 return output

def main():
 raw=json.loads((ROOT/'artefacts/data/sprint11-scheduled-runs.json').read_text())
 evidence_path=ROOT/'artefacts/data/sprint11-slot-evidence.json'
 evidence=json.loads(evidence_path.read_text()) if evidence_path.exists() else None
 output=build_ledger(raw,evidence)
 (ROOT/'artefacts/data/sprint11-schedule-ledger.json').write_text(json.dumps(output,indent=2)+'\n')
 print(json.dumps({x['workflow']:{'runs':len(x['observed_runs']),'slot_coverage':x['slot_coverage']} for x in output['workflows']}))
if __name__=='__main__':main()


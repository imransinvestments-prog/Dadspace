import copy,datetime as dt
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sprint11_schedule_ledger import expected_slots,build_ledger,HOURS,runtime_fingerprint,REQUIRED_RUNTIME,config_hash
UTC=dt.timezone.utc
class ScheduleTests(unittest.TestCase):
 def fixture(self,start=dt.date(2026,10,18),days=1):
  raw={'captured_at':dt.datetime.combine(start+dt.timedelta(days=days),dt.time(),UTC).isoformat(),'workflows':{w:[] for w in HOURS}}
  proofs=[]
  for workflow,hours in HOURS.items():
   for offset in range(days):
    for slot in expected_slots(start+dt.timedelta(days=offset),hours):
     run_id=len(proofs)+1;created=slot+dt.timedelta(minutes=2);finished=slot+dt.timedelta(minutes=8)
     raw['workflows'][workflow].append({'id':run_id,'run_attempt':1,'head_sha':'a'*40,'event':'schedule','status':'completed','conclusion':'success','created_at':created.isoformat(),'updated_at':finished.isoformat(),'html_url':f'https://github.com/example/repo/actions/runs/{run_id}'})
     proofs.append({'workflow':workflow,'expected_at':slot.isoformat(),'run_id':run_id,'run_attempt':1,'head_sha':'a'*40,'evidence_url':f'https://example.org/retained/{run_id}','reviewed_by':'owner','reviewed_at':finished.isoformat()})
  return raw,{'version':1,'assignments':proofs}
 def build(self,raw,proof=None,**kwargs):return build_ledger(raw,proof,hash_fn=lambda sha,w:'same',**kwargs)
 def test_transitive_runtime_changes_invalidate_configuration(self):
  workflow='daily-workers.yml';objects={p:'a'*40 for p in REQUIRED_RUNTIME[workflow]}
  original=runtime_fingerprint(workflow,objects)
  self.assertIsNotNone(original)
  for path in ['.github/workflows/collect-activities.yml','events_worker.py','worker.py','requirements-browser.txt','news_geography.json']:
   changed={**objects,path:'b'*40}
   with self.subTest(path=path):self.assertNotEqual(runtime_fingerprint(workflow,changed),original)
  self.assertNotEqual(runtime_fingerprint(workflow,{**objects,'new_dynamic_adapter.py':'c'*40}),original)
  missing=dict(objects);missing.pop('events_worker.py')
  self.assertIsNone(runtime_fingerprint(workflow,missing))
  self.assertIsNone(config_hash('nonexistent-sprint11-object','daily-workers.yml'))
 def test_originals_worker_and_maintenance_changes_invalidate(self):
  workflow='original-content.yml';objects={p:'a'*40 for p in REQUIRED_RUNTIME[workflow]}
  original=runtime_fingerprint(workflow,objects)
  for path in ['original_content_worker.py','scripts/maintenance-run.py']:
   self.assertNotEqual(runtime_fingerprint(workflow,{**objects,path:'b'*40}),original)
 def test_london_slots_preserve_wall_time_across_clock_change(self):
  before=expected_slots(dt.date(2026,10,24),(7,19));after=expected_slots(dt.date(2026,10,25),(7,19))
  self.assertEqual([s.hour for s in before],[6,18]);self.assertEqual([s.hour for s in after],[7,19]);self.assertEqual((after[0]-before[0]).total_seconds(),25*3600)
 def test_unknown_without_evidence_and_future_unscored(self):
  raw,_=self.fixture();slots=self.build(raw)['workflows'][0]['expected_slots']
  self.assertEqual(slots[0]['state'],'elapsed_unattributed');self.assertEqual(slots[-1]['state'],'future_not_due')
 def test_successful_exact_binding(self):
  raw,proof=self.fixture();workflow=self.build(raw,proof)['workflows'][0]
  self.assertEqual(workflow['expected_slots'][0]['state'],'success');self.assertEqual(workflow['expected_slots'][0]['dispatch_minutes'],2)
  self.assertEqual(workflow['observed_runs'][0]['slot_assignment'],'reviewed_retained_evidence')
 def test_reject_conflicts_reuse_and_identity_mismatch(self):
  raw,proof=self.fixture()
  for field,value in [('run_attempt',2),('head_sha','b'*40),('run_id',999),('evidence_url','http://example.org/log')]:
   bad=copy.deepcopy(proof);bad['assignments'][0][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.build(raw,bad)
  for mode in ['duplicate_slot','reused_url','reused_run']:
   bad=copy.deepcopy(proof)
   if mode=='duplicate_slot':bad['assignments'].append(copy.deepcopy(bad['assignments'][0]))
   elif mode=='reused_url':bad['assignments'][1]['evidence_url']=bad['assignments'][0]['evidence_url']
   else:
    for key in ['run_id','run_attempt','head_sha']:bad['assignments'][1][key]=bad['assignments'][0][key]
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.build(raw,bad)
 def test_failed_late_and_configuration_mismatch(self):
  raw,proof=self.fixture();raw['workflows']['daily-workers.yml'][0]['conclusion']='failure'
  self.assertEqual(self.build(raw,proof)['workflows'][0]['expected_slots'][0]['state'],'failed')
  raw,proof=self.fixture();run=raw['workflows']['daily-workers.yml'][0];slot=dt.datetime.fromisoformat(proof['assignments'][0]['expected_at'])
  run['created_at']=(slot+dt.timedelta(minutes=61)).isoformat();run['updated_at']=(slot+dt.timedelta(minutes=250)).isoformat();proof['assignments'][0]['reviewed_at']=run['updated_at']
  row=self.build(raw,proof)['workflows'][0]['expected_slots'][0]
  self.assertEqual(row['state'],'late');self.assertTrue(row['dispatch_warning']);self.assertTrue(row['completion_warning'])
  changed=build_ledger(raw,proof,hash_fn=lambda sha,w:sha)['workflows'][0]
  self.assertEqual(changed['expected_slots'][0]['state'],'configuration_mismatch')
 def test_seven_day_coverage_separates_feed_acceptance_across_dst(self):
  start=dt.date(2026,10,20);raw,proof=self.fixture(start,7)
  for workflow in self.build(raw,proof,start=start)['workflows']:
   self.assertEqual(len(workflow['expected_slots']),14);self.assertEqual(workflow['slot_coverage'],'met');self.assertEqual(workflow['acceptance'],'not_met');self.assertEqual(workflow['feed_publication_acceptance'],'not_evaluated')
 def test_one_originals_run_cannot_fill_both_opportunities(self):
  self.assertEqual(len(set(expected_slots(dt.date(2026,10,23),(7,9)))),2)
if __name__=='__main__':unittest.main()

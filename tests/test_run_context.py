import unittest
from run_context import github_run_context
class RunContextTests(unittest.TestCase):
 def test_actual_parent_identity_is_retained_without_arbitrary_environment(self):
  env={'GITHUB_RUN_ID':'39164718975','GITHUB_RUN_ATTEMPT':'2','GITHUB_SHA':'a'*40,'GITHUB_EVENT_NAME':'schedule','GITHUB_REPOSITORY':'imransinvestments-prog/Dadspace','SUPABASE_SERVICE_KEY':'not-for-evidence'}
  result=github_run_context(env)
  self.assertEqual(result['github_run_id'],'39164718975')
  self.assertEqual(result['github_run_attempt'],'2')
  self.assertNotIn('not-for-evidence',str(result))
  self.assertEqual(len(result),5)
 def test_local_or_malformed_identity_remains_unknown(self):
  self.assertTrue(all(v is None for v in github_run_context({}).values()))
  self.assertIsNone(github_run_context({'GITHUB_RUN_ID':'123\nsecret'})['github_run_id'])

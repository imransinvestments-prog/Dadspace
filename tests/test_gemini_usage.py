import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from gemini_usage import BudgetExhausted, make_extractor


def response(text='[]', finish='STOP', total=15, usage=True):
    return SimpleNamespace(text=text, candidates=[SimpleNamespace(finish_reason=finish)],
                           usage_metadata=SimpleNamespace(prompt_token_count=10,
                               candidates_token_count=2, thoughts_token_count=3,
                               total_token_count=total) if usage else None)


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'GEMINI_API_KEY': 'fake'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client_patch = patch('google.genai.Client')
        self.client_factory = self.client_patch.start()
        self.addCleanup(self.client_patch.stop)
        self.generate = self.client_factory.return_value.models.generate_content
        self.generate.return_value = response()
        self.sleep = patch('gemini_usage.time.sleep').start()
        self.addCleanup(patch.stopall)

    def caller(self):
        return make_extractor('gemini-3.6-flash', list[dict], 60, RuntimeError)

    def test_explicit_config_and_thinking_accounting(self):
        os.environ.update(GEMINI_THINKING_LEVEL='low', GEMINI_MAX_OUTPUT_TOKENS='1000')
        call = self.caller()
        self.assertEqual(call('hello'), [])
        config = self.generate.call_args.kwargs['config']
        self.assertEqual(config.thinking_config.thinking_level.value.lower(), 'low')
        self.assertEqual(config.max_output_tokens, 1000)
        self.assertEqual(call.metrics['output_tokens'], 5)
        self.assertEqual(call.metrics['thinking_tokens'], 3)
        http = self.client_factory.call_args.kwargs['http_options']
        self.assertEqual(http.timeout, 60000)
        self.assertEqual(http.retry_options.attempts, 1)

    def test_default_preserves_model_settings(self):
        self.caller()('hello')
        config = self.generate.call_args.kwargs['config']
        self.assertIsNone(config.thinking_config)
        self.assertIsNone(config.max_output_tokens)

    def test_budget_checked_before_next_request(self):
        os.environ['GEMINI_RUN_TOKEN_BUDGET'] = '10'
        call = self.caller()
        call('hello')  # An in-flight request may exceed the budget.
        with self.assertRaises(BudgetExhausted):
            call('again')
        self.assertEqual(self.generate.call_count, 1)

    def test_retry_counts_and_attempt_cap(self):
        os.environ['GEMINI_RUN_MAX_ATTEMPTS'] = '1'
        self.generate.side_effect = ValueError('network failed')
        call = self.caller()
        with self.assertRaises(BudgetExhausted):
            call('hello')
        self.assertEqual(call.metrics['api_attempts'], 1)
        self.assertEqual(call.metrics['unknown_usage_attempts'], 1)

    def test_unknown_usage_stops_token_budget(self):
        os.environ['GEMINI_RUN_TOKEN_BUDGET'] = '100'
        self.generate.return_value = response(usage=False)
        call = self.caller()
        call('hello')
        with self.assertRaises(BudgetExhausted):
            call('again')

    def test_truncated_and_malformed_responses_never_accepted(self):
        os.environ['GEMINI_MAX_RETRIES'] = '0'
        for reply in (response('[{}]', finish='MAX_TOKENS'), response('{}'), response('[1]'), response('broken')):
            with self.subTest(reply=reply.text):
                self.generate.return_value = reply
                with self.assertRaises(RuntimeError):
                    self.caller()('hello')

    def test_retry_records_both_responses(self):
        self.generate.side_effect = [response('broken'), response()]
        call = self.caller()
        self.assertEqual(call('hello'), [])
        self.assertEqual(call.metrics['api_attempts'], 2)
        self.assertEqual(call.metrics['total_tokens'], 30)

    def test_invalid_settings_fail_before_request(self):
        for name, value in [('GEMINI_THINKING_LEVEL', 'off'), ('GEMINI_RUN_TOKEN_BUDGET', '-1')]:
            with patch.dict(os.environ, {name: value}):
                with self.assertRaises(ValueError):
                    self.caller()
        self.generate.assert_not_called()

    def test_both_worker_schemas_use_controls(self):
        import worker
        import events_worker
        for factory in (worker.make_gemini_caller, events_worker.make_gemini_caller):
            with self.subTest(factory=factory.__module__):
                call = factory()
                self.assertEqual(call('hello'), [])
                self.assertEqual(call.metrics['api_attempts'], 1)

    def test_budget_stop_does_not_mark_or_save_current_source(self):
        import worker
        os.environ.update(SUPABASE_URL='https://example.supabase.co', SUPABASE_KEY='fake')
        db = Mock()
        db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 'test', 'name': 'Pending source'}]
        extract = Mock(metrics={}, settings={})
        with patch('supabase.create_client', return_value=db), \
             patch.object(worker, 'check_events_table', return_value=None), \
             patch.object(worker, 'make_gemini_caller', return_value=extract), \
             patch.object(worker, 'process_source', side_effect=BudgetExhausted('cap')), \
             patch.object(worker, 'remove_expired_events'), \
             patch.object(worker, 'log_run'), \
             patch.object(worker, 'save_events') as save, \
             patch.object(worker, 'CATEGORY_FILTER', []), \
             patch.object(worker, 'DRY_RUN', False):
            worker.main()
        save.assert_not_called()
        db.table.return_value.update.assert_not_called()
        extract.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()

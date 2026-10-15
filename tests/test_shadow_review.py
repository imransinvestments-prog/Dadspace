import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from shadow_capture import capture_calls
from scripts.replay_shadow import replay, estimate, configure_minimum, score_reference


class ShadowReviewTests(unittest.TestCase):
    def caller(self):
        def call(prompt):
            call.metrics['api_attempts'] += 1
            return [{'title': 'Family workshop', 'event_url': 'https://example.org/event'}]
        call.metrics = {'api_attempts': 0}
        call.settings = {'model': 'gemini'}
        call.json_schema = {'type': 'array', 'items': {'type': 'object'}}
        call.close = Mock()
        return call

    def test_capture_preserves_return_and_caps_sample_without_extra_calls(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory, \
             patch.dict(os.environ, {'SHADOW_CAPTURE_DIR': directory}):
            original = self.caller()
            call = capture_calls(original)
            for _ in range(3):
                self.assertEqual(call('same prompt')[0]['title'], 'Family workshop')
            paths = list(Path(directory).glob('*.json'))
            self.assertEqual(len(paths), 2)
            self.assertEqual(original.metrics['api_attempts'], 3)
            sample = json.loads(paths[0].read_text())
            self.assertEqual(sample['prompt'], 'same prompt')
            self.assertEqual(sample['usage']['api_attempts'], 1)

    def test_capture_io_failure_cannot_fail_production(self):
        with patch.dict(os.environ, {'SHADOW_CAPTURE_DIR': 'unused'}), \
             patch('shadow_capture.Path.mkdir', side_effect=OSError('disk error')):
            call = capture_calls(self.caller())
            self.assertEqual(call('prompt')[0]['title'], 'Family workshop')

    def test_empty_results_do_not_consume_nonempty_sample_slots(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory, \
             patch.dict(os.environ, {'SHADOW_CAPTURE_DIR': directory}):
            original = self.caller()
            call = Mock(side_effect=[[], [{'title': 'Family workshop'}], [], [{'title': 'Family trail'}]],
                        metrics=original.metrics, settings=original.settings,
                        json_schema=original.json_schema, close=original.close)
            wrapped = capture_calls(call)
            for index in range(4):
                wrapped('prompt ' + str(index))
            paths = sorted(Path(directory).glob('*.json'))
            self.assertEqual(len(paths), 2)
            self.assertEqual([json.loads(p.read_text())['prompt'] for p in paths], ['prompt 1', 'prompt 3'])
            self.assertEqual(call.call_count, 4)

    def test_disabled_capture_and_production_error_behavior(self):
        with patch.dict(os.environ, {'SHADOW_CAPTURE_DIR': ''}):
            original = self.caller()
            self.assertIs(capture_calls(original), original)
        original = self.caller()
        original = Mock(side_effect=RuntimeError('original error'), metrics={}, settings={}, close=Mock())
        with patch.dict(os.environ, {'SHADOW_CAPTURE_DIR': 'unused'}):
            with self.assertRaisesRegex(RuntimeError, 'original error'):
                capture_calls(original)('prompt')

    def test_replay_exact_prompts_and_four_request_cap(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            inputs = root / 'inputs'
            inputs.mkdir()
            for i in range(6):
                (inputs / f'sample-{i}.json').write_text(json.dumps({'prompt': 'saved prompt ' + str(i),
                    'schema': {'type': 'array'}, 'raw': [], 'worker': 'events', 'settings': {}, 'usage': {}}))
            generator = Mock(settings={}, metrics={'api_attempts': 0})
            prompts = []
            def generate(prompt, schema):
                prompts.append(prompt)
                generator.metrics['api_attempts'] += 1
                return []
            generator.generate.side_effect = generate
            report = replay(inputs, root / 'output', generator)
            self.assertEqual(prompts, ['saved prompt ' + str(i) for i in range(4)])
            self.assertEqual(len(report['samples']), 4)
            self.assertFalse(report['database_access'])
            self.assertFalse(report['publishing'])

    def test_failure_keeps_partial_report_without_retry(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            (root / 'sample-1.json').write_text(json.dumps({'prompt': 'prompt', 'schema': {},
                'raw': [], 'worker': 'events', 'settings': {}, 'usage': {}}))
            generator = Mock(settings={}, metrics={}, generate=Mock(side_effect=RuntimeError('failure')))
            with self.assertRaises(RuntimeError):
                replay(root, root / 'output', generator)
            generator.generate.assert_called_once()
            self.assertTrue((root / 'output/results.json').exists())
            report = json.loads((root / 'output/results.json').read_text())
            self.assertEqual(report['samples'][0]['status'], 'failed; no retry or fallback')
            self.assertEqual(report['samples'][0]['error_type'], 'RuntimeError')
            self.assertIsNone(report['samples'][0]['comparison'])
            self.assertNotIn('failure', json.dumps(report))

    def test_cost_unknown_without_rates_and_thinking_is_not_double_counted(self):
        usage = {'prompt_tokens': 100, 'output_tokens': 50, 'thinking_tokens': 20}
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(estimate(usage, 'BASELINE'))
        with patch.dict(os.environ, {'BASELINE_INPUT_USD_PER_MILLION': '1', 'BASELINE_OUTPUT_USD_PER_MILLION': '2'}):
            self.assertAlmostEqual(estimate(usage, 'BASELINE'), 0.0002)
            self.assertIsNone(estimate(dict(usage, unknown_usage_attempts=1), 'BASELINE'))

    def test_minimum_preserves_captured_model_and_records_real_setting(self):
        generator = Mock(provider='gemini', settings={})
        self.assertTrue(configure_minimum({'settings': {'model': 'gemini-3.6-flash'}}, generator))
        self.assertEqual(generator.model, 'gemini-3.6-flash')
        self.assertEqual(generator.thinking_level, 'minimal')
        self.assertEqual(generator.settings['thinking_level'], 'minimal')
        self.assertEqual(generator.temperature, 0)
        self.assertTrue(configure_minimum({'settings': {'model': 'gemini-3.8-flash'}}, generator))
        self.assertEqual(generator.thinking_level, 'low')

    def test_unknown_gemini_model_is_not_replayed_or_substituted(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            (root / 'sample-1.json').write_text(json.dumps({'prompt': 'prompt', 'schema': {},
                'raw': [], 'worker': 'events', 'settings': {'model': 'future-model'}, 'usage': {}}))
            generator = Mock(provider='gemini', settings={}, metrics={})
            report = replay(root, root / 'output', generator, configure_minimum)
            generator.generate.assert_not_called()
            self.assertEqual(report['samples'][0]['status'], 'unsupported-model; no paid request')

    def test_content_failure_continues_across_workers_but_budget_stops(self):
        from gemini_usage import BudgetExhausted
        from llm_provider import IncompleteOutputError
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            for index, worker in enumerate(['activities', 'activities', 'civic', 'civic']):
                (root / f'sample-{index}.json').write_text(json.dumps({'prompt': str(index),
                    'schema': {}, 'raw': [], 'worker': worker, 'settings': {}, 'usage': {}}))
            gen = Mock(settings={}, metrics={}, generate=Mock(side_effect=[
                IncompleteOutputError('OpenAI', {'finish_reason': 'max_output_tokens'}), [], [], []]))
            report = replay(root, root / 'out', gen)
            self.assertEqual([s['worker'] for s in report['samples']],
                             ['activities', 'civic', 'activities', 'civic'])
            self.assertEqual(report['content_failures'], 1)
            self.assertEqual(report['samples'][0]['diagnostics']['finish_reason'], 'max_output_tokens')
            gen.generate = Mock(side_effect=BudgetExhausted('budget'))
            with self.assertRaises(BudgetExhausted):
                replay(root, root / 'out2', gen)
            gen.generate.assert_called_once()

    def test_oversized_baseline_is_deferred_without_paid_replay(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            (root / 'sample-1.json').write_text(json.dumps({'prompt': 'source', 'schema': {},
                'raw': [], 'worker': 'civic', 'settings': {},
                'usage': {'output_tokens': 8000, 'thinking_tokens': 1000}}))
            gen = Mock(settings={'max_output_tokens': 3000}, metrics={})
            report = replay(root, root / 'out', gen)
            gen.generate.assert_not_called()
            self.assertIn('needs-reviewed-chunks', report['samples'][0]['status'])

    def test_source_score_keeps_ambiguous_identity_and_cost_unknown(self):
        reference = {'kind': 'human-reviewed-source', 'expected': [
            {'id': 'one', 'evidence': 'children', 'fields': {'event_url': 'https://x/a',
                'start_date': None, 'age_range': '3-5'}}]}
        score = score_reference(reference, [{'event_url': 'https://x/a', 'age_range': '0-5'}])
        self.assertEqual(score['candidates'][0]['differing_fields'], ['age_range'])
        self.assertIsNone(score['accepted_listing_count'])
        with patch.dict(os.environ, {'BASELINE_INPUT_USD_PER_MILLION': '1',
                                    'BASELINE_OUTPUT_USD_PER_MILLION': '1'}):
            self.assertIsNone(estimate({}, 'BASELINE'))


if __name__ == '__main__':
    unittest.main()

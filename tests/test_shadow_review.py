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
        reference = {'kind': 'source-reviewed', 'expected': [
            {'id': 'one', 'evidence': 'children', 'fields': {'event_url': 'https://x/a',
                'start_date': None, 'age_range': '3-5'}}]}
        score = score_reference(reference, [{'event_url': 'https://x/a', 'age_range': '0-5'}])
        self.assertEqual(score['candidates'][0]['differing_fields'], ['age_range'])
        self.assertIsNone(score['accepted_listing_count'])
        with patch.dict(os.environ, {'BASELINE_INPUT_USD_PER_MILLION': '1',
                                    'BASELINE_OUTPUT_USD_PER_MILLION': '1'}):
            self.assertIsNone(estimate({}, 'BASELINE'))

    def test_identity_scoring_pairs_same_titles_by_venue_and_normalises_fields(self):
        reference = {'kind': 'source-reviewed', 'expected': [
            {'id': 'camden', 'evidence': 'x', 'fields': {'title': 'Rhyme Time', 'listing_type': 'activity', 'venue_name': 'Camden Town Library', 'postcode': 'NW1 1BD'}},
            {'id': 'kilburn', 'evidence': 'x', 'fields': {'title': 'Rhyme Time', 'listing_type': 'activity', 'venue_name': 'Kilburn Library', 'postcode': 'NW6 5UH'}},
            {'id': 'class', 'evidence': 'x', 'fields': {'title': 'El Recreo Spanish', 'age_range': '4 years to 12 years',
                                                         'event_url': 'https://x.org/classes/'}},
            {'id': 'missing', 'evidence': 'x', 'fields': {'title': 'Toy Library'}}],
            'excluded': [{'id': 'adult', 'evidence': 'Murder Mystery Halloween Dinner', 'reason': 'Adult dinner event'}]}
        rows = [{'title': 'Rhyme time', 'listing_type': 'activity', 'venue_name': 'Kilburn Library', 'venue_address': '12-22 Kilburn High Road, NW6 5UH'},
                {'title': 'Rhyme Time (under 5s)', 'listing_type': 'event', 'location': 'Camden Town Library, 218 Eversholt Street', 'postcode': 'nw11bd'},
                {'title': 'El Recreo Spanish Online for Kids', 'age_range': '4-12', 'event_url': 'https://x.org/classes?utm=1'},
                {'title': 'Murder Mystery Halloween Dinner', 'listing_type': 'event'},
                {'title': 'Antiques fair'}]
        score = score_reference(reference, rows)
        by_id = {c['id']: c for c in score['candidates']}
        self.assertEqual(by_id['camden']['output_index'], 1)
        self.assertEqual(by_id['camden']['differing_fields'], ['listing_type'])
        self.assertEqual((by_id['kilburn']['output_index'], by_id['kilburn']['differing_fields']), (0, []))
        self.assertEqual((by_id['class']['output_index'], by_id['class']['differing_fields']), (2, []))
        self.assertEqual(by_id['missing']['status'], 'missing; review required')
        self.assertEqual([x['id'] for x in score['excluded_returned']], ['adult'])
        self.assertEqual(score['extra_output_indices'], [4])
        self.assertEqual(score['summary'], {'expected': 4, 'matched': 3, 'fields_checked': 11, 'fields_correct': 10,
            'classification_checked': 2, 'classification_correct': 1, 'excluded_returned': 1, 'extras': 1})
        self.assertIsNone(score['accepted_listing_count'])

    def test_a_different_explicit_date_or_postcode_is_a_different_record(self):
        reference = {'kind': 'source-reviewed', 'expected': [
            {'id': 'a', 'evidence': 'x', 'fields': {'title': 'Pumpkin Patch', 'start_date': '2026-10-23'}},
            {'id': 'b', 'evidence': 'x', 'fields': {'title': 'Pumpkin Patch', 'postcode': 'M3 5DW'}}]}
        score = score_reference(reference, [{'title': 'Pumpkin Patch', 'start_date': '2026-11-01', 'postcode': 'M4 4DR'}])
        self.assertEqual(score['summary']['matched'], 0)

    def test_every_cohort_reference_identifies_its_own_records(self):
        cohort = Path(__file__).resolve().parents[1] / 'artefacts' / 'shadow-cohorts' / 'quality-2026-10-23'
        samples = sorted(cohort.glob('sample-*.json'))
        self.assertEqual(len(samples), 15)
        for path in samples:
            reference = json.loads(path.read_text(encoding='utf-8'))['reference']
            perfect = [dict(item['fields']) for item in reference['expected']]
            summary = score_reference(reference, perfect)['summary']
            with self.subTest(sample=path.name):
                self.assertEqual(summary['matched'], summary['expected'])
                self.assertEqual(summary['fields_correct'], summary['fields_checked'])
                self.assertEqual((summary['extras'], summary['excluded_returned']), (0, 0))

    def test_dispatch_sample_cap_and_ceilings(self):
        from scripts.replay_shadow import max_samples, check_ceilings
        with patch.dict(os.environ, {}):
            os.environ.pop('SHADOW_MAX_SAMPLES', None)
            self.assertEqual(max_samples(), 4)  # the automatic shadow keeps its old cap
        for value, ok in (('16', True), ('17', False), ('0', False)):
            with patch.dict(os.environ, {'SHADOW_MAX_SAMPLES': value}):
                if ok:
                    self.assertEqual(max_samples(), 16)
                else:
                    self.assertRaises(ValueError, max_samples)
        for name, bad in (('LLM_RUN_TOKEN_BUDGET', '250001'), ('LLM_MAX_OUTPUT_TOKENS', '8001'), ('LLM_RUN_MAX_ATTEMPTS', '17')):
            with patch.dict(os.environ, {name: bad}):
                self.assertRaises(ValueError, check_ceilings)
        with patch.dict(os.environ, {'LLM_RUN_TOKEN_BUDGET': '250000', 'LLM_MAX_OUTPUT_TOKENS': '8000', 'LLM_RUN_MAX_ATTEMPTS': '16'}):
            check_ceilings()


if __name__ == '__main__':
    unittest.main()

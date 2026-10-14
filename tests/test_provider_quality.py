import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts import review_provider_quality as review


class QualityReviewTests(unittest.TestCase):
    def test_resume_reuses_pages_and_completed_variants_without_paid_replay(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            output = root / 'provider-quality-review'
            output.mkdir()
            row = {'title': 'Family craft', 'family_evidence': 'Children welcome'}
            previous = {'database_access': False, 'publishing': False, 'total_tokens': 100,
                        'api_attempts': 3, 'sources': [
                            {'source': 'Cardiff Libraries', 'variants': {
                                'gemini': {'rows': [row]}, 'openai': {'rows': [row]}}},
                            {'source': 'Museum Wales', 'variants': {}}]}
            (output / 'results.json').write_text(json.dumps(previous), encoding='utf-8')
            for name, url in review.SOURCES:
                (output / (name.replace(' ', '-') + '-snapshot.json')).write_text(json.dumps({
                    'url': url, 'documents': [(url, '<main><h1>Family craft</h1><p>Children welcome</p></main>')]}), encoding='utf-8')
            calls = []
            def factory():
                metrics = {'api_attempts': 0, 'total_tokens': 0}
                def call(prompt):
                    calls.append(os.environ['EXTRACTION_LLM_PROVIDER'])
                    metrics.update(api_attempts=1, total_tokens=10)
                    return [row]
                call.metrics, call.close = metrics, lambda: None
                return call
            with patch.object(review, 'ROOT', root), patch.dict(os.environ, {}), \
                 patch.object(review.events_worker, 'install_quality_rules'), \
                 patch.object(review.events_worker, '_venue_client'), \
                 patch.object(review.events_worker, 'make_gemini_caller', side_effect=factory), \
                 patch.object(review.worker, 'fetch_html_requests') as fetch, \
                 patch.object(review.worker, 'robots_allows') as robots, \
                 patch.object(review.worker, 'clean_events', side_effect=lambda raw, *args: raw):
                review.main()
            self.assertEqual(calls, ['gemini', 'openai'])
            fetch.assert_not_called()
            robots.assert_not_called()
            result = json.loads((output / 'results.json').read_text(encoding='utf-8'))
            self.assertEqual(result['api_attempts'], 5)
            self.assertEqual(result['total_tokens'], 120)
            self.assertEqual(result['sources'][1]['comparison']['missing'], [])

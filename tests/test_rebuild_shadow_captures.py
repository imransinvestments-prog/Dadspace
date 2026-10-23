import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))

try:
    import bs4, pydantic, requests  # noqa: F401,E401
    DEPS = True
except ImportError:
    DEPS = False


@unittest.skipIf(not DEPS, 'collector dependencies required; covered by shadow-review CI')
class RebuildTests(unittest.TestCase):
    def test_rebuild_records_the_production_prompt_without_secrets_or_model_calls(self):
        import events_worker
        import rebuild_shadow_captures as rebuild
        from prepare_shadow_chunks import prepare
        seen = {}
        def process_source(source, extract, today):
            seen.update(source=source, env={k: os.environ.get(k) for k in ('SUPABASE_KEY', 'GEMINI_API_KEY', 'FETCH_ENGINE', 'CATEGORIES')})
            extract('instructions\nCONTENT:\nRhyme Time\nWednesdays, 11am')
            return 'ok_zero', [], 'hash', '0 extracted', {}
        source = {'id': 'x', 'name': 'Camden Council', 'url': 'https://example.org/whats-on', 'category': 'councils',
                  'last_hash': 'stored', 'last_success_at': '2026-10-23'}
        with tempfile.TemporaryDirectory() as tmp:
            sources = Path(tmp) / 'sources.json'
            sources.write_text(json.dumps([source]), encoding='utf-8')
            out = Path(tmp) / 'out'
            with patch.dict(os.environ, {'SUPABASE_KEY': 'secret', 'GEMINI_API_KEY': 'secret'}), \
                    patch.object(sys, 'argv', ['x', str(sources), 'events-civic', str(out)]), \
                    patch.object(events_worker, 'install_quality_rules'), \
                    patch.object(events_worker.base, 'process_source', process_source):
                rebuild.main()
            capture = json.loads((out / 'camden-council-1.json').read_text(encoding='utf-8'))
        self.assertEqual(seen['env'], {'SUPABASE_KEY': None, 'GEMINI_API_KEY': None, 'FETCH_ENGINE': 'requests',
                                       'CATEGORIES': 'councils,heritage_parks,niche_venues'})
        self.assertIsNone(seen['source']['last_hash'])  # forced re-read
        self.assertEqual(capture['prompt'], 'instructions\nCONTENT:\nRhyme Time\nWednesdays, 11am')
        self.assertEqual((capture['worker'], capture['raw'], capture['usage']), ('events-civic', [], {}))
        self.assertTrue(capture['settings']['rebuilt_offline'])
        self.assertIn('properties', json.dumps(capture['schema']))  # the real response schema
        content = 'Rhyme Time\nWednesdays, 11am'
        manifest = {'prompt_sha256': hashlib.sha256(capture['prompt'].encode()).hexdigest(), 'reviewer': 'test',
                    'chunks': [{'start': 0, 'end': len(content), 'complete_records': True, 'all_candidates_reviewed': True,
                                'expected': [{'id': 'r', 'evidence': 'Rhyme Time', 'fields': {'listing_type': 'activity'}}],
                                'excluded': []}]}
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(len(prepare(capture, manifest, Path(tmp) / 'cohort')), 1)


if __name__ == '__main__':
    unittest.main()

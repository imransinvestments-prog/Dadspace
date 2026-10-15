import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_shadow_chunks import prepare


class ChunkTests(unittest.TestCase):
    def fixture(self):
        capture = {'prompt': 'rules\nCONTENT:\nFamily A\nFamily B', 'worker': 'civic',
                   'schema': {}, 'settings': {}}
        manifest = {'prompt_sha256': hashlib.sha256(capture['prompt'].encode()).hexdigest(),
                    'reviewer': 'reviewer', 'chunks': []}
        for start, end, text in [(0, 9, 'Family A'), (9, 17, 'Family B')]:
            manifest['chunks'].append({'start': start, 'end': end, 'complete_records': True,
                'all_candidates_reviewed': True, 'expected': [{'id': text, 'evidence': text,
                    'fields': {'title': text}}], 'excluded': []})
        return capture, manifest

    def test_complete_partition_preserves_every_character_and_reference(self):
        capture, manifest = self.fixture()
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            rows = prepare(capture, manifest, Path(directory) / 'cohort')
            self.assertEqual(''.join(r['prompt'].split('\nCONTENT:\n')[1] for r in rows),
                             capture['prompt'].split('\nCONTENT:\n')[1])
            self.assertEqual(rows[0]['reference']['kind'], 'human-reviewed-source')
            self.assertEqual(rows[0]['usage'], {})

    def test_gaps_missing_evidence_and_unreviewed_boundaries_fail_before_write(self):
        for defect in ('gap', 'evidence', 'boundary', 'hash'):
            capture, manifest = self.fixture()
            if defect == 'gap':
                manifest['chunks'][1]['start'] += 1
            elif defect == 'evidence':
                manifest['chunks'][0]['expected'][0]['evidence'] = 'invented'
            elif defect == 'hash':
                manifest['prompt_sha256'] = 'wrong'
            else:
                manifest['chunks'][0]['complete_records'] = False
            with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
                output = Path(directory) / 'cohort'
                with self.assertRaises(ValueError):
                    prepare(capture, manifest, output)
                self.assertFalse(output.exists())


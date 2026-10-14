"""Guard the orchestration contract: unrelated feeds cannot suppress collection."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def job_block(text, name):
    return re.search(r'^  ' + name + r':\n(.*?)(?=^  [a-z_]+:|\Z)', text,
                     re.MULTILINE | re.DOTALL).group(1)


class PipelineIsolationTests(unittest.TestCase):
    def test_scheduled_feeds_only_depend_on_the_schedule_gate(self):
        text = (ROOT / '.github/workflows/daily-workers.yml').read_text()
        for name in ('news', 'venue_reference', 'civic', 'activities', 'deals'):
            with self.subTest(feed=name):
                block = job_block(text, name)
                self.assertEqual(re.findall(r'^    needs: (.*)$', block, re.MULTILINE), ['gate'])
                self.assertNotRegex(block, r'needs\.(?:news|civic|activities|deals|venue_reference)\.')

    def test_manual_combined_collection_has_no_success_dependency(self):
        text = (ROOT / '.github/workflows/collect-all.yml').read_text()
        self.assertNotRegex(job_block(text, 'activities'), r'^    (?:needs|if):')


if __name__ == '__main__':
    unittest.main()

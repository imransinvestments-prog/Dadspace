import datetime as dt
import unittest
from unittest.mock import patch

import worker


class ExtractionCacheTests(unittest.TestCase):
    today = dt.date(2026, 10, 11)
    source = {"name": "Museum", "url": "https://example.org/events"}
    html = """<nav>Menu revision 1</nav><main><p>Children must attend with an adult.</p>
    <article><h2>Family pottery</h2><p>October 15, 2026, 2pm. Ages 5+, £8.</p>
    <a href='/events/pottery'>Book pottery</a></article></main><footer>Visits 123</footer>"""

    def test_listing_appears_once_and_context_remains(self):
        text, _ = worker.prepare_content(self.html, self.source['url'])
        self.assertEqual(text.count('Family pottery'), 1)
        for evidence in ('Children must attend with an adult.', 'Ages 5+', '£8',
                         'https://example.org/events/pottery'):
            self.assertIn(evidence, text)
        self.assertNotIn('Menu revision', text)

    def test_navigation_edits_do_not_invalidate_but_price_and_audience_do(self):
        def digest(html):
            content, _ = worker.prepare_content(html, self.source['url'])
            return worker.extraction_cache_hash(content, self.source, self.today)
        original = digest(self.html)
        self.assertEqual(original, digest(self.html.replace('Menu revision 1', 'Menu revision 2')
                                         .replace('Visits 123', 'Visits 456')))
        self.assertNotEqual(original, digest(self.html.replace('£8', '£12')))
        self.assertNotEqual(original, digest(self.html.replace('Children must', 'Only adults must')))

    def test_version_rules_and_whitespace(self):
        key = worker.extraction_cache_hash('Listing October 15 2026', self.source, self.today)
        self.assertEqual(key, worker.extraction_cache_hash('Listing  October\n15 2026', self.source, self.today))
        with patch.object(worker, 'EXTRACTION_CACHE_VERSION', 'new-schema'):
            self.assertNotEqual(key, worker.extraction_cache_hash('Listing October 15 2026', self.source, self.today))
        with patch.object(worker, 'build_prompt', return_value='new instructions'):
            self.assertNotEqual(key, worker.extraction_cache_hash('Listing October 15 2026', self.source, self.today))

    def test_success_timestamp_refresh_and_invalid_dates(self):
        source = dict(self.source, last_success_at='2026-10-10T10:00:00Z')
        self.assertTrue(worker.extraction_cache_fresh(source, self.today))
        source['last_success_at'] = '2026-10-01T10:00:00Z'
        self.assertFalse(worker.extraction_cache_fresh(source, self.today))
        source['last_success_at'] = 'broken'
        self.assertFalse(worker.extraction_cache_fresh(source, self.today))
        with patch.object(worker, 'EXTRACTION_REFRESH_DAYS', 0):
            self.assertFalse(worker.extraction_cache_fresh(self.source, self.today))

    def test_relative_date_results_do_not_carry_into_another_day(self):
        next_day = self.today + dt.timedelta(days=1)
        self.assertNotEqual(worker.extraction_cache_hash('Family event tomorrow', self.source, self.today),
                            worker.extraction_cache_hash('Family event tomorrow', self.source, next_day))
        self.assertEqual(worker.extraction_cache_hash('Family event October 15 2026', self.source, self.today),
                         worker.extraction_cache_hash('Family event October 15 2026', self.source, next_day))

    def test_cache_hit_avoids_call_and_force_reread_calls(self):
        html = self.html + '<p>' + 'Extra evidence. ' * 30 + '</p>'
        content, _ = worker.prepare_content(html, self.source['url'])
        source = dict(self.source, last_hash=worker.extraction_cache_hash(content, self.source, self.today),
                      last_success_at='2026-10-11T00:00:00Z')
        calls = []
        def extract(prompt):
            calls.append(prompt)
            return []
        with patch.object(worker, 'robots_allows', return_value=(True, '')), \
             patch.object(worker, 'fetch_source_html', return_value=html), \
             patch.dict('os.environ', {'FORCE_REREAD': 'false'}):
            result = worker.process_source(source, extract, self.today)
            self.assertEqual(result[0], 'unchanged')
            self.assertEqual(result[4]['cache_hits'], 1)
            self.assertEqual(calls, [])
            with patch.dict('os.environ', {'FORCE_REREAD': 'true'}):
                self.assertEqual(worker.process_source(source, extract, self.today)[0], 'ok_zero')
            self.assertEqual(len(calls), 1)

    def test_jsonld_duplicate_removed_without_losing_visible_evidence(self):
        data = '<script type="application/ld+json">{"@type":"Event","name":"Pottery"}</script>'
        text, _ = worker.prepare_content(data + data + '<main>Children welcome October 15 2026</main>', self.source['url'])
        self.assertEqual(text.count('"@type": "Event"'), 1)
        self.assertIn('Children welcome', text)


if __name__ == '__main__':
    unittest.main()

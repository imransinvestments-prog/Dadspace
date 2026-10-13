import unittest
from family_grounding import grounded, filter_grounded


class GroundingTests(unittest.TestCase):
    def documents(self):
        return [('https://example.org/events', '<main><article><h2>Dark Winter Tales with Mat Troy</h2>'
                 '<p>A talk about local legends.</p></article><article><h2>Family craft</h2>'
                 '<p>Children and families welcome.</p></article></main>')]

    def test_model_audience_and_score_are_not_source_evidence(self):
        row = dict(title='Dark Winter Tales with Mat Troy', audience='families', family_relevance=5)
        self.assertFalse(grounded(row, self.documents(), 'Children and families welcome.'))

    def test_neighbouring_listing_cannot_supply_quote(self):
        row = dict(title='Dark Winter Tales with Mat Troy', family_evidence='Children and families welcome.')
        self.assertFalse(grounded(row, self.documents(), row['family_evidence']))

    def test_exact_local_quote_accepts_and_invented_or_unsupplied_quote_rejects(self):
        row = dict(title='Family craft', family_evidence='Children and families welcome.')
        self.assertTrue(grounded(row, self.documents(), row['family_evidence']))
        self.assertFalse(grounded(row, self.documents(), 'Only a truncated adult talk'))
        row['family_evidence'] = 'This is suitable for young children'
        self.assertFalse(grounded(row, self.documents(), row['family_evidence']))

    def test_global_banner_and_navigation_are_not_listing_evidence(self):
        docs = [('https://example.org', '<header>Children welcome</header><main>'
                 '<h1>The Creative Cwtsh</h1><p>A creative space.</p></main>')]
        self.assertFalse(grounded(dict(title='The Creative Cwtsh', family_evidence='Children welcome'),
                                  docs, 'Children welcome'))

    def test_link_only_neighbouring_cards_cannot_supply_quote(self):
        docs = [('https://example.org', '<main><div><a href="/adult">Adult talk</a>'
                 '<div><a href="/craft">Craft club</a><p>Children welcome</p></div></div></main>')]
        self.assertFalse(grounded(dict(title='Adult talk', family_evidence='Children welcome'),
                                  docs, 'Children welcome'))

    def test_rejected_rows_are_counted_and_no_audience_fallback(self):
        stats = {}
        rows = filter_grounded([{'title': 'The Creative Cwtsh', 'audience': 'families'}],
                               self.documents(), 'Family craft', stats)
        self.assertEqual(rows, [])
        self.assertEqual(stats['ungrounded_family_evidence'], 1)

    def test_explicit_child_age_band_is_evidence_but_senior_age_band_is_not(self):
        docs = [('https://example.org', '<main><h1>Museum Makers</h1><p>Ages 7-11</p></main>')]
        self.assertTrue(grounded(dict(title='Museum Makers', family_evidence='Ages 7-11'), docs, 'Ages 7-11'))
        docs = [('https://example.org', '<main><h1>Creative Cwtsh</h1><p>Ages 55-75</p></main>')]
        self.assertFalse(grounded(dict(title='Creative Cwtsh', family_evidence='Ages 55-75'), docs, 'Ages 55-75'))

import unittest
from canonical_venue import resolve


class DB:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []
    def table(self, name):
        self.calls.append(name)
        return self
    def select(self, fields): return self
    def eq(self, key, value):
        self.filter = (key, value)
        self.calls.append((key, value))
        return self
    def limit(self, count): self.cap = count; return self
    def execute(self):
        key, value = self.filter
        return type('Result', (), {'data': [r for r in self.rows if str(r.get(key)) == value][:self.cap]})()


def row(id='a', name='Library', public=True, target=None):
    return dict(id=id, venue_name=name, postcode='W4 2AB', public_visible=public, merged_into=target)


class CanonicalVenueTests(unittest.TestCase):
    def test_unique_public_match_uses_equality(self):
        db = DB([row()])
        self.assertEqual(resolve(db, 'Library', 'W4 2AB')[0], 'a')
        self.assertIn(('postcode', 'W4 2AB'), db.calls)

    def test_missing_evidence_and_unmatched_never_create_places(self):
        db = DB([])
        self.assertIsNone(resolve(db, 'Private appointment', '')[0])
        self.assertEqual(db.calls, [])
        self.assertEqual(resolve(db, 'New venue', 'W4 2AB')[1], 'unmatched_place')

    def test_duplicate_names_hidden_or_excess_candidates_are_unknown(self):
        for rows, reason in [([row(),row('b')],'ambiguous_place'),
                             ([row(public=False)],'unreviewed_place'),
                             ([row(str(i)) for i in range(21)],'candidate_limit')]:
            self.assertEqual(resolve(DB(rows), 'Library', 'W4 2AB'), (None, reason))

    def test_reviewed_merge_aliases_converge_on_public_canonical(self):
        rows = [row(public=False,target='b'),row('b',name='Canonical Library')]
        self.assertEqual(resolve(DB(rows), 'Library', 'W4 2AB')[0], 'b')
        rows.append(row('c',public=False,target='b'))
        self.assertEqual(resolve(DB(rows), 'Library', 'W4 2AB')[0], 'b')

    def test_alias_cycle_missing_target_and_hidden_target_stay_unknown(self):
        for rows in ([row(target='a')],[row(target='missing')],
                     [row(target='b'),row('b',name='Target',public=False)]):
            self.assertIsNone(resolve(DB(rows), 'Library', 'W4 2AB')[0])

    def test_same_similarity_is_not_identity(self):
        self.assertIsNone(resolve(DB([row(name='Library Annex')]),'Library','W4 2AB')[0])


if __name__ == '__main__': unittest.main()

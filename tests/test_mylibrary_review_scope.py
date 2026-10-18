import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('source_review',Path(__file__).resolve().parents[1]/'scripts/validate_mylibrary_sources.py')
review=importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewScopeTests(unittest.TestCase):
    def test_bounded_family_does_not_accept_unchecked_portals(self):
        selected=review.selected_sources('mylibrary_calendar')
        self.assertEqual([name for name,_ in selected],['Sutton library'])
        self.assertEqual(len(review.selected_sources('all')),3)
        self.assertEqual(len(review.selected_sources('library_portal')),2)
        results=[{'name':'Sutton library','status':'ok','rows':[{'dedupe_key':'one'}],
                  'stats':{'gemini_logical_calls':0}} for _ in range(2)]
        self.assertEqual(review.acceptance_errors(results,selected),[])
        self.assertEqual(len(review.acceptance_errors(results)),2)


if __name__=='__main__':unittest.main()

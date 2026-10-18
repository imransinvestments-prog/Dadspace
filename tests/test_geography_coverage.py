import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('coverage_check',Path(__file__).parents[1]/'scripts/check_geography_coverage.py')
coverage=importlib.util.module_from_spec(spec);spec.loader.exec_module(coverage)


class CoverageEvidenceTests(unittest.TestCase):
    def test_empty_is_separate_from_unavailable_and_incomplete(self):
        empty=coverage.assess('venues',200,{'venues':[],'total':0,'hasMore':False})
        self.assertEqual(empty['status'],'observed_empty')
        self.assertEqual(empty['completeness'],'endpoint_result')
        self.assertIsNone(coverage.assess('venues',503,{})['count'])
        partial=coverage.assess('venues',200,{'venues':[{'id':'a'}],'total':50,'hasMore':True})
        self.assertEqual(partial['count'],1)
        self.assertEqual(partial['completeness'],'first_page')

    def test_bad_sample_duplicate_and_failure_payloads_do_not_pass(self):
        for body in [{'events':[],'loadFailed':True},{'events':[],'isSample':True},{'events':'bad'},
                     {'events':[{'id':'a'},{'id':'a'}]},{'events':[{'id':'a'}],'total':0}]:
            result=coverage.assess('events',200,body)
            self.assertIsNone(result['count'])
            self.assertIn(result['status'],('failed','unavailable'))

    def test_ni_case_cannot_make_any_network_request(self):
        result=coverage.observe({'id':'ni','state':'blocked_licence','reason':'licence'},'https://not-requested.invalid')
        self.assertEqual(len(result),4)
        self.assertTrue(all(row['status']=='blocked_licence' and row['count'] is None for row in result))

    def test_events_without_total_are_not_a_complete_inventory(self):
        result=coverage.assess('events',200,{'events':[]})
        self.assertEqual(result['status'],'observed_empty')
        self.assertEqual(result['completeness'],'not_established')


if __name__=='__main__': unittest.main()

import json,unittest
from pathlib import Path
from scout_sessions import extract_group,collect_scouts

class ScoutSessionsTests(unittest.TestCase):
    def manifest(self):return json.loads(Path('artefacts/data/ds10-scout-group-routes-2026-10-12.json').read_text(encoding='utf8'))
    def fixture(self,name):return (Path('tests/fixtures/scouts')/(name+'.html')).read_text(encoding='utf8')
    def group(self,prefix):return next(x for x in self.manifest()['groups'] if x['title'].startswith(prefix))
    def test_age_sections_multiple_nights_and_unavailable_section(self):
        bar=self.group('1st Bar Hill');items,_=extract_group(self.fixture('1st-bar-hill'),bar,bar['url'],{})
        self.assertEqual(len(items),4);self.assertIn('4 to 6',items[0]['ages'])
        over=self.group('1st Over');items,issues=extract_group(self.fixture('1st-over-st-marys-scout-group'),over,over['url'],{})
        self.assertEqual(len(items),2);self.assertIn('Beavers: explicitly unavailable',issues)
        will=self.group('1st Willingham');items,_=extract_group(self.fixture('1st-willingham'),will,will['url'],{})
        self.assertEqual(len(items),4);self.assertEqual(len({x['proposal_key'] for x in items}),4)
        self.assertTrue(all(x['dates']=='' for x in items))
    def test_named_colonies_and_waiting_list_do_not_cross_sections(self):
        group=self.group('1st Whittlesford');items,issues=extract_group(self.fixture('duxford'),group,group['url'],{})
        self.assertEqual(len(items),2)
        self.assertTrue(any('Wildwood' in x['name'] for x in items));self.assertTrue(any('Forest' in x['name'] for x in items))
        self.assertEqual(len(issues),3)
    def test_missing_meetings_and_conflicting_ages_remain_visible(self):
        milton=dict(self.group('50th'),section='Squirrels');items,issues=extract_group(self.fixture('milton-squirrels'),milton,milton['url'],{})
        self.assertFalse(items);self.assertTrue(issues)
        fulbourn=dict(self.group('57th'),section='Beavers');items,issues=extract_group(self.fixture('fulbourn-beavers'),fulbourn,fulbourn['url'],{})
        self.assertEqual(len(items),1);self.assertTrue(issues);self.assertIn('resolve eligibility',items[0]['notes'])
        self.assertIn('confirm section meeting place',items[0]['notes'])
    def test_one_failed_route_does_not_erase_other_groups_or_invent_unknowns(self):
        manifest=self.manifest();bar=self.group('1st Bar Hill');unknown=self.group('32nd')
        manifest['groups']=[dict(bar,url='https://example.com/fails'),bar,unknown]
        def fetch(url):
            if 'example.com' in url:raise ValueError('HTTP 403')
            return self.fixture('1st-bar-hill'),url
        items,issues,statuses=collect_scouts(fetch,manifest)
        self.assertEqual(len(items),4);self.assertEqual(len(statuses),3)
        self.assertTrue(any('HTTP 403' in x for x in issues));self.assertTrue(any('2021' in x for x in issues))
    def test_plural_age_heading_does_not_pollute_age_value(self):
        group=dict(self.group('57th'),section='Scouts')
        items,_=extract_group(self.fixture('fulbourn-scouts'),group,group['url'],{})
        self.assertEqual(items[0]['ages'],'10½ to 14 years')

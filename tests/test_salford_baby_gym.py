import unittest
from salford_baby_gym import parse_baby_gym
class BabyGymTests(unittest.TestCase):
    def test_term_time_marker_and_duplicate_rise_table_are_scoped(self):
        table='<table><tr><th>Day</th><th>Venue</th><th>Time</th></tr><tr><td>Tuesday</td><td>Boothstown Community Centre</td><td>10:30 – 11:15*</td></tr><tr><td>Thursday</td><td>Worsley Leisure Centre</td><td>14:00 – 14:45</td></tr></table>'
        items=parse_baby_gym('Baby Gym 9 months + '+table+table)
        self.assertEqual(len(items),2);self.assertIn('term-time only',items[0]['schedule']);self.assertNotIn('term-time only',items[1]['schedule'])
        self.assertTrue(all(x['dates']=='' and x['ages']=='9 months+' for x in items))
    def test_missing_eligibility_or_table_fails_closed(self):
        for body in ['No timetable','9 months + No timetable']:
            with self.assertRaises(ValueError):parse_baby_gym(body)

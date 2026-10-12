import unittest
from shredder_sessions import parse_shredder

class ShredderTests(unittest.TestCase):
    def test_coach_day_drafts_keep_child_and_adult_schedules_separate(self):
        page='<main><div>Peter Higginson Senior Coach / SKATE Peter runs groups for children on Saturdays and an adults class on Monday evenings.<a href="mailto:shredderskateschool@gmail.com">GROUP</a></div><div>Seb Fisher Senior Coach / SKATE He offers group and private sessions on Sundays.<a href="mailto:shredderskateschool@gmail.com">GROUP</a></div></main>'
        items,issues=parse_shredder(page,'https://www.shredderskateschool.co.uk/book-trumpington','Trumpington Skatepark','Trumpington, Cambridge','Lessons are suitable for ages 5 and above.')
        self.assertEqual(len(items),2);self.assertEqual(len(issues),2)
        self.assertEqual([x['schedule'].split(';')[0] for x in items],['Saturday','Sunday'])
        self.assertTrue(all(x['dates']=='' and x['ages']=='5+' and 'exact session clock time' in x['notes'] for x in items))
        self.assertTrue(all('Monday' not in x['schedule'] for x in items))
    def test_private_only_and_price_text_do_not_generate_holiday_occurrences(self):
        items,issues=parse_shredder('<main>Private weekdays. Holiday Clubs - £50</main>','https://www.shredderskateschool.co.uk/book-jesus-green','Jesus Green Skatepark','Cambridge','Lessons are suitable for ages 5 and above.')
        self.assertFalse(items);self.assertEqual(len(issues),1)
    def test_booking_and_age_changes_require_requalification(self):
        page='<div>Coach Senior Coach / SKATE Saturdays<a href="https://example.com">GROUP</a></div>'
        with self.assertRaises(ValueError):parse_shredder(page,'https://www.shredderskateschool.co.uk/book-trumpington','Park','Cambridge','No minimum age')
        with self.assertRaises(ValueError):parse_shredder(page,'https://www.shredderskateschool.co.uk/book-trumpington','Park','Cambridge','Lessons are suitable for ages 5 and above.')

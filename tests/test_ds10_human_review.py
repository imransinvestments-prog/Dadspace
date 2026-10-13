import unittest
from scripts.validate_ds10_human_review import validate

class HumanReviewValidationTests(unittest.TestCase):
    def test_threshold_requires_all_agreed_ids_and_answers(self):
        sample=dict(rows=[dict(id=str(i)) for i in range(100)])
        review=dict(sample='ds10-human-review-2026-10-11.json',reviewer='Imran Tajuddin',reviewed_at='2026-10-11',
                    answers={str(i):dict(relevant='yes',current='yes',actionable='yes' if i<90 else 'no') for i in range(100)})
        self.assertTrue(validate(sample,review)['quality_target_met'])
        review['answers']['0']['current']=''
        self.assertFalse(validate(sample,review)['complete'])
        review['answers']['0']['current']='yes'
        review['answers']['0']['actionable']='no'
        self.assertFalse(validate(sample,review)['quality_target_met'])
        review['answers']['0']['actionable']='yes'
        review['answers']['foreign']=review['answers'].pop('0')
        self.assertFalse(validate(sample,review)['complete'])

if __name__=='__main__': unittest.main()

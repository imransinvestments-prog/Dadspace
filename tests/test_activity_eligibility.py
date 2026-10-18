import unittest
from activity_eligibility import age_evidence,build_ledger,full_postcode,location_evidence,PILOT


class EligibilityTests(unittest.TestCase):
    def test_numeric_and_developmental_ages_preserve_unknowns(self):
        for text in ('0-5','18 months to 8 years','3 mths - 5 yrs','2.5 – 4 years','Under 5','For under 5s','baby','pre-schoolers','5-11 years','8 weeks to 12 months'):
            self.assertEqual(age_evidence(text)['state'],'eligible',text)
        for text in ('6-11 years','7 years to 11 years','6+ years'):
            self.assertEqual(age_evidence(text)['state'],'outside',text)
        for text in (None,'Year 2 to Year 4','For the whole family','Walking to School Age','11 months to 4 years 11 months','10-2 years'):
            self.assertEqual(age_evidence(text)['state'],'unknown',text)

    def test_visible_canonical_venue_precedes_postcode_and_hidden_does_not_leak(self):
        row={'venue_public_visible':True,'venue_latitude':PILOT[0],'venue_longitude':PILOT[1],
             'postcode':'CF14 2HU'}
        postcodes={'CF142HU':{'latitude':51.6,'longitude':-3.2}}
        self.assertEqual(location_evidence(row,postcodes)['state'],'local')
        row['venue_public_visible']=False
        self.assertEqual(location_evidence(row,postcodes)['state'],'outside')
        self.assertEqual(location_evidence({},postcodes)['state'],'unknown')

    def test_postcode_in_location_and_failed_lookup_are_explicit(self):
        self.assertEqual(full_postcode('Library, W3 9LN'),'W39LN')
        row={'location':'Library, W3 9LN'}
        self.assertEqual(location_evidence(row,{'W39LN':{'latitude':PILOT[0],'longitude':PILOT[1]}})['state'],'local')
        self.assertEqual(location_evidence(row,{'W39LN':{}})['state'],'unknown')

    def test_virtual_delivery_cannot_inherit_physical_pilot_eligibility(self):
        row={'location':'Virtual classroom, W3 9LN','venue_public_visible':True,
             'venue_latitude':PILOT[0],'venue_longitude':PILOT[1]}
        self.assertEqual(location_evidence(row,{})['state'],'unknown')

    def test_deduplicates_identity_without_discarding_unknown_or_national_supply(self):
        a={'id':'a','identity_key':'same','age_range':'0-5','location':'W3 9LN','source_id':'one','category':'story'}
        b={**a,'id':'b'}
        unknown={**a,'id':'c','identity_key':'unknown','location':None,'age_range':None}
        ledger=build_ledger({'captured_at':'fixture','rows':[a,b,unknown]},
                            {'W39LN':{'latitude':PILOT[0],'longitude':PILOT[1]}})
        self.assertEqual(ledger['input_count'],3)
        self.assertEqual(ledger['unique_opportunities'],2)
        self.assertEqual(ledger['pilot_eligible_count'],1)
        self.assertEqual(ledger['rows'][0]['duplicate_row_ids'],['b'])
        self.assertEqual(ledger['unknown_age_count'],1)
        self.assertEqual(ledger['unknown_location_count'],1)


if __name__=='__main__':unittest.main()

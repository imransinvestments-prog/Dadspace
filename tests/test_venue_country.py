import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock

from venue_country import enrich_country_candidate, lookup_postcodes, normalize_postcode, resolve_country

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('places_review',ROOT/'scripts/build_places_data_review.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)

class CountryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=json.loads((ROOT/'artefacts/data/library-postcode-evidence-2026-10-17.json').read_text(encoding='utf-8'))

    def test_real_four_nation_fixtures(self):
        for postcode,country in [('SW1A1AA','England'),('EH11YZ','Scotland'),('CF101EP','Wales'),('BT15GS','Northern Ireland')]:
            with self.subTest(country=country):
                self.assertEqual(resolve_country(postcode,self.evidence['results'][postcode])['country'],country)

    def test_missing_invalid_conflicting_and_mismatched_values_stay_unknown(self):
        valid=copy.deepcopy(self.evidence['results']['SW1A1AA'])
        for postcode,result,authority in [('',None,None),('W2 5DU',None,None),('W1A 1AA',valid,None),('SW1A1AA',valid,'W06000015')]:
            self.assertIsNone(resolve_country(postcode,result,authority)['country'])
        valid['country']='Scotland'
        self.assertIsNone(resolve_country('SW1A1AA',valid)['country'])

    def test_candidate_retains_source_and_separates_derived_evidence(self):
        row={'postcode':'sw1a 1aa','payload':{'Name':'A library','Reporting service code':'E09000033'}}
        result=enrich_country_candidate(row,self.evidence['results'])
        self.assertEqual(result['country'],'England')
        self.assertEqual(result['payload']['Name'],'A library')
        self.assertEqual(result['payload']['_dadspace_country']['validated_postcode'],'SW1A 1AA')

    def test_network_failure_stays_unknown(self):
        with patch('urllib.request.urlopen',side_effect=OSError('offline')):
            found=lookup_postcodes(['SW1A 1AA'])
        self.assertEqual(resolve_country('SW1A1AA',found['SW1A1AA'])['reason'],'lookup_unavailable')

    def test_duplicate_postcodes_bounded_batches_and_exact_response_matching(self):
        response=MagicMock();response.__enter__.return_value=response
        response.read.return_value=json.dumps({'status':200,'result':[{'query':'SW1A1AA','result':self.evidence['results']['SW1A1AA']}]}).encode()
        with patch('urllib.request.urlopen',return_value=response) as request:
            found=lookup_postcodes(['SW1A 1AA','sw1a1aa'])
        self.assertEqual(request.call_count,1)
        self.assertEqual(found['SW1A1AA']['country'],'England')

    def test_review_cohort_reconciles_and_sql_is_guarded_and_defaults_to_rollback(self):
        plan=json.loads((ROOT/'artefacts/data/places-data-review-2026-10-17.json').read_text(encoding='utf-8'))
        self.assertEqual(sum(plan['nation_totals'].values()),3440)
        self.assertEqual(plan['nation_totals'],{'England':3392,'Unknown':48})
        sql=review.build_sql(plan)
        for guard in ['Concurrent change/missing row','Library cohort changed','Unapproved field changed','Existing correction audit','Missing reviewed-field protection','rollback;']:
            self.assertIn(guard,sql)
        self.assertTrue(review.build_sql(plan,commit=True).rstrip().endswith('commit;'))
        duplicated=copy.deepcopy(plan);duplicated['changes'].append(duplicated['changes'][0])
        with self.assertRaises(ValueError):review.build_sql(duplicated)
        invalid=copy.deepcopy(plan);invalid['changes'][0]['country']='Scotland'
        with self.assertRaises(ValueError):review.build_sql(invalid)

class LibraryImportTests(unittest.TestCase):
    def test_known_country_preserved_and_missing_country_filled_on_repeat_import(self):
        with patch.dict(sys.modules,{'requests':MagicMock(),'supabase':MagicMock()}):
            import venue_reference_loader_v2 as loader
        db=MagicMock()
        candidate={'country':'England'}
        with patch.object(loader,'DRY_RUN',False):
            loader.enrich(db,{'id':'library','country':'Wales'},candidate)
            db.table.assert_not_called()
            loader.enrich(db,{'id':'library','country':None},candidate)
            db.table.return_value.update.assert_called_once_with({'country':'England'})
        db.reset_mock()
        with patch.object(loader,'DRY_RUN',True):
            loader.enrich(db,{'id':'library','country':None},candidate)
        db.table.assert_not_called()

if __name__=='__main__':unittest.main()

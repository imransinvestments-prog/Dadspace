import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('catalogue',ROOT/'scripts/geography_catalogue.py')
catalogue=importlib.util.module_from_spec(spec);spec.loader.exec_module(catalogue)
REFERENCE=json.loads((ROOT/'geography/reference.json').read_text(encoding='utf-8'))
PACK=json.loads((ROOT/'geography/test-pack.json').read_text(encoding='utf-8'))


class GeographyCatalogueTests(unittest.TestCase):
    def test_complete_administrative_catalogue_and_deliberate_sample(self):
        catalogue.validate(REFERENCE)
        self.assertEqual(sum(a['kind']=='council' for a in REFERENCE['areas']),361)
        self.assertEqual({a['name'] for a in REFERENCE['areas'] if a['kind']=='nation'}, {'England','Wales','Scotland','Northern Ireland'})
        self.assertEqual(len(PACK['cases']),30)
        self.assertEqual(len(REFERENCE['postcodes']),28)
        self.assertEqual(len({c['expected_region'] for c in PACK['cases'] if c.get('expected_nation')=='England'}),9)
        self.assertEqual(sum(c['state']=='blocked_licence' for c in PACK['cases']),2)
        self.assertTrue(any(c['postcode']=='W3 9LN' for c in PACK['cases']))

    def test_bad_reference_cannot_generate_sql(self):
        for mutate in (
            lambda r:r['areas'].append(r['areas'][0]),
            lambda r:r['postcodes'][0].update(postcode='BT1 5GS'),
            lambda r:r['postcodes'][0].update(council_code='missing'),
            lambda r:r['postcodes'][0].update(nation_code='S92000003'),
            lambda r:r['postcodes'][0].update(latitude=float('nan')),
            lambda r:r['postcodes'][0].update(terminated='199001',introduced='200001'),
            lambda r:r['relationships'][0].update(parent=r['relationships'][0]['child']),
        ):
            reference=copy.deepcopy(REFERENCE);mutate(reference);output=io.StringIO()
            with self.assertRaises(ValueError): catalogue.emit_seed(reference,output)
            self.assertEqual(output.getvalue(),'')

    def test_postal_hierarchy_is_independent_and_normalized(self):
        self.assertEqual(catalogue.normalize(' w39ln '),'W3 9LN')
        self.assertEqual([row[0] for row in catalogue.postal_nodes('W3 9LN')],['P:W','P:W3','P:W3 9'])
        for value in ['BT1 5GS','INVALID','']:
            with self.assertRaises(ValueError): catalogue.normalize(value)

    def test_onspd_stream_preserves_termination_and_rejects_ni(self):
        (ROOT/'review').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'review') as directory:
            path=Path(directory)/'sample.csv'
            path.write_text('pcds,lat,long,lad,ctry,dointr,doterm\nW3 9LN,51.5,-0.2,E09000009,E92000001,198001,202601\nBT1 5GS,54.5,-5.9,N09000003,N92000002,198001,\n')
            rows=catalogue.read_onspd(path)
            self.assertEqual(next(rows)['terminated'],'202601')
            with self.assertRaises(ValueError): next(rows)

    def test_seed_is_deterministic_and_retains_licence_and_hash(self):
        first,second=io.StringIO(),io.StringIO()
        self.assertEqual(catalogue.emit_seed(REFERENCE,first),catalogue.emit_seed(REFERENCE,second))
        self.assertEqual(first.getvalue(),second.getvalue())
        self.assertIn('pg_advisory_xact_lock',first.getvalue())
        self.assertNotIn("'BT1 5GS'",first.getvalue())
        compact=copy.deepcopy(REFERENCE);compact['postcodes'][0]['postcode']='w39ln'
        normalized=io.StringIO();catalogue.emit_seed(compact,normalized)
        self.assertEqual(first.getvalue(),normalized.getvalue())


if __name__=='__main__': unittest.main()

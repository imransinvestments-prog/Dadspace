"""Regression checks for wrapper validation, save enrichment and dry-run evidence."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import news_worker_locality as worker


def result(**changes):
    return dict(i=0, region="england", geo_scope="local", geo_region="",
                admin_area="Cambridgeshire", locality="Cambridge", relevance=4,
                category="activities", summary="Family sessions", why_it_matters="Free play", **changes)


class LocalityTests(unittest.TestCase):
    def setUp(self):
        worker._review.clear()
        worker._geo_by_article.clear()

    def test_missing_metadata_is_unclassified_not_nationwide(self):
        self.assertEqual(worker.normalise_geo({"region": "england"}), worker.UNKNOWN_GEO)
        self.assertIsNotNone(worker.raw_geo_problem({"region": "england"}))

    def test_normalisation_and_supported_regions(self):
        data = result()
        self.assertEqual(worker.normalise_geo(data)["locality"], "cambridge")
        data.update(locality="Glasgow City Council", admin_area="", region="scotland")
        self.assertEqual(worker.normalise_geo(data)["locality"], "glasgow_city")
        self.assertEqual(worker.geo_region("Yorkshire and Humber"), "yorkshire_and_the_humber")
        data.update(region="wales", geo_scope="regional", geo_region="South Wales")
        self.assertEqual(worker.normalise_geo(data), worker.UNKNOWN_GEO)

    def test_invalid_raw_types_and_scope(self):
        for field, value in [("geo_scope", "invalid"), ("locality", ["cambridge"]), ("region", "Europe")]:
            data = result(); data[field] = value
            self.assertIsNotNone(worker.raw_geo_problem(data))
        data = result(); data.update(locality="", admin_area="")
        self.assertEqual(worker.normalise_geo(data), worker.UNKNOWN_GEO)

    def test_save_attaches_metadata_and_safe_unknown(self):
        worker._geo_by_article[("A", "Source")] = worker.normalise_geo(result())
        rows = [{"title": "A", "source_name": "Source"}, {"title": "B", "source_name": "Source"}]
        with patch.object(worker, "_original_save_items", side_effect=lambda r: r) as save:
            worker.save_items_with_geo(rows)
        save.assert_called_once_with(rows)
        self.assertEqual(rows[0]["locality"], "cambridge")
        self.assertIsNone(rows[1]["geo_scope"])

    def run_self_test(self, include_geo):
        def score(batch):
            rows = []
            for i, (_, expected) in enumerate(worker.SELF_TEST_CASES):
                row = {"i": i, "region": expected["region"]}
                if include_geo:
                    row.update(geo_scope=expected["geo_scope"], geo_region="", admin_area="", locality="")
                    row.update({key: value for key, value in expected.items() if key != "region"})
                rows.append(row)
            return rows
        def core_test():
            worker.core.gemini_score([{"i": 0, "title": "Original", "source": "test"}])
            return 0
        with patch.object(worker, "_original_gemini_score", side_effect=score), patch.object(worker.core, "self_test", side_effect=core_test), patch.object(worker.core, "sb"), contextlib.redirect_stdout(io.StringIO()):
            return worker.self_test()

    def test_self_test_rejects_missing_raw_geography(self):
        self.assertEqual(self.run_self_test(False), 1)

    def test_self_test_accepts_representative_valid_geography(self):
        self.assertEqual(self.run_self_test(True), 0)

    def test_dry_run_emits_geography_without_saving(self):
        source = {"id": 1, "name": "test", "feed_url": "https://example.test/feed", "filter_mode": "none"}
        entry = {"title": "Cambridge family play sessions announced", "link": "https://example.test/story", "summary": "Free sessions for local children"}
        output = io.StringIO()
        with patch.object(worker.core, "DRY_RUN", True), patch.object(worker.core, "out_of_time", return_value=False), patch.object(worker.core, "load_sources", return_value=[source]), patch.object(worker.core, "load_existing", return_value=(set(), set(), [])), patch.object(worker.core, "fetch_feed", return_value=[entry]), patch.object(worker.core, "mark_source"), patch.object(worker.core, "load_existing_stories", return_value=[]), patch.object(worker.core, "assign_stories", return_value={}), patch.object(worker, "_original_gemini_score", return_value=[result()]), patch.object(worker, "_original_save_items") as save, patch.object(worker, "_original_log_run"), contextlib.redirect_stdout(output):
            self.assertEqual(worker.run(), 0)
        save.assert_not_called()
        self.assertIn("NEWS GEOGRAPHY", output.getvalue())
        self.assertIn('"locality": "cambridge"', output.getvalue())
        self.assertEqual(worker._review[0]["stage"], "collection")


if __name__ == "__main__":
    unittest.main()

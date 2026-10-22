import contextlib
import io
import unittest
import sys
from pathlib import Path
from unittest.mock import patch, Mock
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import news_worker as core
import news_worker_locality as locality

class NewsMaintenanceTests(unittest.TestCase):
    def test_source_selector_only_reads_one_active_feed(self):
        response=Mock();response.json.return_value=[]
        with patch.dict(core.os.environ,{"NEWS_SOURCE_ID":"7"}),patch.object(core,"sb",return_value=response) as sb:
            core.load_sources()
            self.assertEqual(sb.call_args.kwargs["params"]["id"],"eq.7")
            self.assertEqual(sb.call_args.kwargs["params"]["active"],"eq.true")
        with patch.dict(core.os.environ,{"NEWS_SOURCE_ID":"7&active=eq.false"}),patch.object(core,"sb") as sb:
            with self.assertRaises(ValueError):core.load_sources()
            sb.assert_not_called()
    def test_one_large_feed_is_capped_and_targeted_retry_never_touches_global_cleanup(self):
        source={"id":7,"name":"Approved test feed","feed_url":"https://example.com/feed","filter_mode":"none"}
        entries=[{"title":f"Family story number {i} with distinct details","link":f"https://example.com/{i}"} for i in range(25)]
        with patch.dict(core.os.environ,{"NEWS_SOURCE_ID":"7"}),patch.object(core,"DRY_RUN",False),patch.object(core,"MAX_NEW_PER_RUN",300),patch.object(core,"load_sources",return_value=[source]),patch.object(core,"load_existing",return_value=(set(),set(),[])),patch.object(core,"fetch_feed",return_value=entries),patch.object(core,"mark_source"),patch.object(core,"out_of_time",return_value=False),patch.object(core,"entry_date",return_value=None),patch.object(core,"prefilter",return_value=None),patch.object(core,"is_near_duplicate",return_value=False),patch.object(core,"gemini_score",return_value=[]) as score,patch.object(core,"log_run"),patch.object(core,"delete_old") as cleanup,contextlib.redirect_stdout(io.StringIO()):
            core.run()
            self.assertEqual(sum(len(c.args[0]) for c in score.call_args_list),10)
            cleanup.assert_not_called()
    def test_targeted_failure_records_health_but_does_not_pause_source(self):
        with patch.dict(core.os.environ,{"NEWS_SOURCE_ID":"7"}),patch.object(core,"DRY_RUN",False),patch.object(core,"sb") as sb:
            core.mark_source({"id":7,"name":"Feed","consecutive_failures":999},False,RuntimeError("failed"))
            self.assertNotIn("active",sb.call_args.kwargs["json_body"])
    def test_remote_denials_never_retry(self):
        for status in (401,402,403,429):
            response=requests.Response();response.status_code=status
            denial=requests.HTTPError(response=response)
            with patch.object(core.requests,"post",side_effect=denial) as post,patch.object(core.time,"sleep") as sleep:
                with self.assertRaises(RuntimeError):core.gemini_json("offline test")
                post.assert_called_once();sleep.assert_not_called()
    def test_live_wrapper_reports_failed_and_missing_evidence(self):
        for stats in (None,{"sources_ok":1,"fatal_error":1},{"sources_ok":1,"batches_failed":1},{"sources_ok":1,"sources_failed":1}):
            def fake():locality._run_stats=stats
            with patch.object(core,"run",side_effect=fake),patch.object(core,"DRY_RUN",False):
                self.assertEqual(locality.run(),1)
    def test_run_row_explains_a_failure_without_job_logs(self):
        stats={"sources_ok":3,"sources_failed":2,"scored":4,"batches_failed":0}
        feeds=["Google News: parenting: HTTP Error 503","Google News: money: HTTP Error 503"]
        with patch.dict(core.os.environ,{"GITHUB_RUN_ID":"39258943242","GITHUB_EVENT_NAME":"schedule"}),patch.object(core,"sb") as sb,contextlib.redirect_stdout(io.StringIO()):
            locality._review.clear()
            core.log_run(stats,failing_feeds=feeds)
        details=sb.call_args.kwargs["json_body"]["details"]
        self.assertEqual(details["status"],"failed")
        self.assertEqual(details["reasons"],["2 feed(s) failed"])
        self.assertEqual(details["failed_sources"],feeds)
        self.assertEqual(details["github"]["run_id"],"39258943242")
        self.assertEqual(details["stats"]["scored"],4)
        self.assertEqual(details["locality"],{"classified":0,"warnings":0})
        # The exit code follows the recorded status, so the two can never disagree.
        def fake():locality._run_stats=stats
        with patch.object(core,"run",side_effect=fake),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(locality.run(),1)
        with patch.object(core,"sb") as sb,contextlib.redirect_stdout(io.StringIO()):
            core.log_run({"sources_ok":5,"scored":0})
        self.assertEqual(sb.call_args.kwargs["json_body"]["details"]["status"],"ok")
if __name__=="__main__":unittest.main()

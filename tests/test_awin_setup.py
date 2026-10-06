import importlib.util
import pathlib
import unittest
from unittest.mock import Mock, patch

import deals_source_adapters as adapters

spec = importlib.util.spec_from_file_location("enable_awin", pathlib.Path(__file__).resolve().parents[1] / "scripts/enable-awin.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class AwinSetupTests(unittest.TestCase):
    def test_credentials_never_sent_to_configured_foreign_endpoint(self):
        with patch.dict("os.environ", {"AWIN_API_TOKEN": "secret", "AWIN_PUBLISHER_ID": "123"}), patch.object(adapters.requests, "post") as post:
            for url in ("https://evil.example/promotions", "https://api.awin.com/publisher/999/promotions"):
                self.assertEqual(adapters.fetch_awin({"url": url})[0], "configuration_invalid")
            post.assert_not_called()

    def test_redirects_are_not_followed(self):
        response = Mock(status_code=302)
        with patch.dict("os.environ", {"AWIN_API_TOKEN": "secret", "AWIN_PUBLISHER_ID": "123"}), patch.object(adapters.requests, "post", return_value=response) as post:
            self.assertEqual(adapters.fetch_awin({"url": "config://awin"})[:2], ("http_302", []))
            self.assertFalse(post.call_args.kwargs["allow_redirects"])

    def test_activation_requires_successful_access_and_readback(self):
        for status in ("configuration_missing", "http_401", "incomplete", "empty"):
            database = Mock(side_effect=[[{"id": 7, "url": "config://awin", "active": False}], None, [{"active": True}]])
            with patch.object(setup.worker, "_SB_URL", "https://example.com"), patch.object(setup.worker, "_SB_KEY", "test"), patch.object(setup.worker, "sb", database), patch.object(setup, "fetch_awin", return_value=(status, [], "")):
                self.assertEqual(setup.main(True), 0 if status == "empty" else 1)
            self.assertEqual(database.call_count, 3 if status == "empty" else 1)

    def test_read_only_does_not_activate(self):
        database = Mock(return_value=[{"id": 7, "url": "config://awin", "active": False}])
        with patch.object(setup.worker, "_SB_URL", "https://example.com"), patch.object(setup.worker, "_SB_KEY", "test"), patch.object(setup.worker, "sb", database), patch.object(setup, "fetch_awin", return_value=("ok", [{}], "")):
            self.assertEqual(setup.main(False), 0)
        database.assert_called_once()

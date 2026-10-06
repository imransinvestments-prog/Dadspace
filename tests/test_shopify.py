import json
import unittest
from unittest.mock import patch
import deals_shopify as s
import deals_worker as worker
from deals_quality import value_reason
from deals_source_adapters import fetch_source
from deals_verification import verify_offer


def product(available=True, price=900):
    return {"id": 1, "handle": "baby-hat", "title": "Baby hat", "description": "Baby hat was £100 now £9 kids eat free with an adult",
            "variants": [{"id": 2, "title": "0-12 months", "price": price, "available": available, "compare_at_price": 1800}]}


class ShopifyTests(unittest.TestCase):
    def setUp(self):
        self.feed, self.shop = next(iter(s.SHOPS.items()))
        self.url = "https://" + self.shop["host"] + "/products/baby-hat"

    def test_no_unreviewed_or_foreign_requests(self):
        with patch.object(s.requests, "get") as get:
            self.assertEqual(s.fetch_shopify({"url": "https://evil.invalid/collection.atom"})[0], "unsupported_url")
            self.assertEqual(s.read("https://localhost/products/hat", self.shop)[0], "unsupported_url")
            self.assertFalse(s.allowed("https://user@" + self.shop["host"] + "/products/hat", self.shop))
            get.assert_not_called()

    def test_variant_identity_and_compare_at_not_value(self):
        raw = s.rows(product(), self.url, self.shop)[0]
        deal = worker.normalise(raw)
        self.assertEqual(deal["price"], 9)
        self.assertIn("variant=2", deal["link"])
        self.assertEqual(deal["dedupe_key"], worker.normalise(raw)["dedupe_key"])
        self.assertTrue(value_reason(deal).startswith("unsupported_value"))
        self.assertIsNone(deal["was_price"])

    def test_sold_out_subscription_and_invalid_prices(self):
        self.assertEqual(s.rows(product(False), self.url, self.shop)[0]["source_status"], "unavailable")
        p = product(); p["variants"][0]["requires_selling_plan"] = True
        self.assertEqual(s.rows(p, self.url, self.shop)[0]["source_status"], "unavailable")
        for value in (True, -1, float("nan"), "900"):
            self.assertEqual(s.rows(product(price=value), self.url, self.shop), [])

    def test_json_never_executes_and_requires_handle(self):
        text = '<script>window.product = ' + json.dumps(product()) + '; danger();</script>'
        self.assertEqual(s.product_json(text, "baby-hat")["id"], 1)
        self.assertIsNone(s.product_json(text, "wrong"))
        analytics = product(); analytics["variants"][0]["price"] = {"amount": 9, "currencyCode": "GBP"}
        mixed = '<script>' + json.dumps(analytics) + '</script>' + text
        self.assertEqual(s.product_json(mixed, "baby-hat")["variants"][0]["price"], 900)

    def test_feed_dispatch_and_duplicate_product_links(self):
        feed = f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><link href="{self.url}"/></entry><entry><link href="{self.url}"/></entry></feed>'
        page = '<script>' + json.dumps(product()) + '</script><script>Shopify.shop="kite"; currency="GBP";</script>'
        with patch.object(s, "read", side_effect=[("ok", feed), ("ok", '<feed xmlns="http://www.w3.org/2005/Atom"/>'), ("ok", page)]), patch.object(s.time, "sleep"):
            status, rows, info = fetch_source({"source_type": "direct", "url": self.feed}, None)
        self.assertEqual(status, "ok"); self.assertEqual(len(rows), 1)
        self.assertIn("bounded sample", info)

    def test_repeated_page_and_partial_failure_do_not_publish(self):
        feed = f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><link href="{self.url}"/></entry></feed>'
        with patch.object(s, "read", return_value=("ok", feed)):
            self.assertEqual(s.fetch_shopify({"url": self.feed})[:2], ("incomplete", []))
        with patch.object(s, "read", side_effect=[("ok", feed), ("http_403", "")]):
            self.assertEqual(s.fetch_shopify({"url": self.feed})[:2], ("http_403", []))

    def test_variant_reverification_price_and_stock(self):
        deal = worker.normalise(s.rows(product(), self.url, self.shop)[0])
        for p, expected in ((product(), "comparison_unconfirmed"), (product(False), "source_unavailable"), (product(price=1000), "price_changed")):
            with patch.object(s, "read", return_value=("ok", '<script>' + json.dumps(p) + '</script>currency="GBP"')):
                self.assertEqual(verify_offer(deal)[0], expected)

    def test_reviewed_evidence_allows_value_and_is_rechecked(self):
        raw = s.rows(product(), self.url, self.shop)[0]
        evidence = {raw["identity"]: {"reviewer": "Test reviewer", "evidence_url": self.url,
                    "current_price": 9, "regular_price": 18, "regular_price_phrase": "Regular price £18",
                    "valid_until": "2099-01-01T00:00:00Z"}}
        text = '<script>' + json.dumps(product()) + '</script>Regular price £18 currency="GBP"'
        with patch.object(s.Path, "read_text", return_value=json.dumps(evidence)):
            s.reviewed_comparison(raw, product(), text)
            deal = worker.normalise(raw)
            self.assertIsNone(value_reason(deal))
            self.assertEqual(deal["was_price"], 18)
            with patch.object(s, "read", return_value=("ok", text)):
                self.assertIsNone(verify_offer(deal)[0])
            with patch.object(s, "read", return_value=("ok", text.replace("Regular price £18", ""))):
                self.assertEqual(verify_offer(deal)[0], "comparison_unconfirmed")
            evidence[raw["identity"]]["valid_until"] = "2020-01-01T00:00:00Z"
        with patch.object(s.Path, "read_text", return_value=json.dumps(evidence)):
            fresh = s.rows(product(), self.url, self.shop)[0]
            s.reviewed_comparison(fresh, product(), text)
            self.assertEqual(fresh["value_evidence_status"], "unsupported_shopify_comparison")

    def test_currency_is_not_inferred_from_a_stale_schema(self):
        self.assertFalse(s.gbp('Shopify.currency = {"active":"USD"}; "priceCurrency":"GBP"'))
        self.assertFalse(s.gbp('currency="USD"'))
        self.assertFalse(s.gbp('no currency'))
        self.assertTrue(s.gbp('Shopify.currency = {"active":"GBP"};'))

    def test_redirects_blocked_and_oversize_rejected(self):
        with patch.object(s.requests, "get") as get:
            response = get.return_value.__enter__.return_value
            response.status_code = 302
            self.assertEqual(s.read(self.url, self.shop)[0], "http_302")
            self.assertFalse(get.call_args.kwargs["allow_redirects"])
            response.status_code = 200
            response.iter_content.return_value = [b"x" * (s.MAX_BYTES + 1)]
            self.assertEqual(s.read(self.url, self.shop)[0], "oversize_page")


if __name__ == "__main__":
    unittest.main()

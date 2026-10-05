import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta, timezone

import deals_worker as worker
import deals_source_adapters as adapters
from deals_verification import verify_offer
from deals_quality import canonical_link, prices, value_reason


def raw(title="Baby car seat now £150 was £200", **changes):
    result = adapters._raw(title=title, link="https://example.com/product?variant=blue&code=DAD&utm_source=feed")
    result.update(changes)
    return result


class DealsTests(unittest.TestCase):
    def test_pagination_and_partial_failure(self):
        def response(items, page, last=2):
            result = Mock(status_code=200)
            result.json.return_value = {"data": items, "meta": {"last_page": last}}
            return result
        first, second = response([{"id": 1}], 1), response([{"id": 2}], 2)
        request = Mock(side_effect=[first, second])
        status, items, _ = adapters._pages(request, ("data",), 100, "Test")
        self.assertEqual((status, len(items)), ("ok", 2))
        self.assertEqual(request.call_count, 2)
        request = Mock(side_effect=[first, Mock(status_code=429)])
        self.assertEqual(adapters._pages(request, ("data",), 100, "Test")[:2], ("http_429", []))

    def test_repeated_pages_do_not_publish_partial_batch(self):
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"id": 1}], "meta": {"last_page": 2}}
        self.assertEqual(adapters._pages(Mock(return_value=response), ("data",), 100, "Test")[:2], ("incomplete", []))

    def test_source_verification_does_not_fetch_arbitrary_urls(self):
        with patch("deals_verification.requests.get") as request:
            self.assertEqual(verify_offer({"link": "http://127.0.0.1/admin"})[0], "verification_unsupported_source")
            self.assertEqual(verify_offer({"link": "https://merchant.example.com", "source_status": "active"}), (None, "source-api"))
        request.assert_not_called()

    def test_source_page_checks_status_content_and_availability(self):
        deal = {"link": "https://www.hotukdeals.com/deals/123", "title": "Baby cot"}
        for status, text, expected in ((200, "<h1>Baby cot</h1>", None), (404, "", "source_unavailable"),
                                       (403, "", "verification_unavailable"), (200, "<title>Just a moment</title>", "verification_unavailable"),
                                       (200, '<h1>Baby cot</h1><script type="application/ld+json">{"offers":{"availability":"https://schema.org/OutOfStock"}}</script>', "source_unavailable")):
            response = Mock(status_code=status)
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            response.iter_content.return_value = [text.encode()]
            with patch("deals_verification.requests.get", return_value=response) as request:
                self.assertEqual(verify_offer(deal)[0], expected)
                self.assertFalse(request.call_args.kwargs["allow_redirects"])

    def test_structured_sale_price_beats_old_price_in_title(self):
        self.assertEqual(prices(raw(merchant_price="150"), "Car seat was £200 now £150", ""), (150, 200, 25))

    def test_leading_source_price_beats_conditional_title_price(self):
        deal = worker.normalise(raw("Baby carrier (£54 with wishlist)", description_raw="£63.99. Requires a wishlist aged 15 days."))
        self.assertEqual(deal["price"], 63.99)
        self.assertIn("15 days", deal["description"])
        self.assertIsNotNone(value_reason(deal))

    def test_ambiguous_amounts_are_not_guessed(self):
        self.assertEqual(prices({}, "Baby carrier £54 or £63.99", "")[0], None)

    def test_rrp_is_not_previous_selling_price(self):
        self.assertEqual(prices({}, "Baby cot £150 RRP £300", ""), (None, None, None))
        self.assertEqual(prices({"merchant_price": "150"}, "Baby cot RRP £300", ""), (150, None, None))

    def test_absolute_savings_qualify(self):
        self.assertIsNone(value_reason({"price": 250, "was_price": 300, "discount_pct": 16.7}))

    def test_rounding_does_not_cross_value_threshold(self):
        self.assertIsNotNone(value_reason({"price": 8.005, "was_price": 10, "discount_pct": 20}))

    def test_dry_run_never_writes_pipeline_logs(self):
        with patch.object(worker, "DRY_RUN", True), patch.object(worker, "sb") as database:
            worker.log_run(0, {})
        database.assert_not_called()

    def test_relevance_does_not_rescue_missing_value(self):
        self.assertIn("unsupported_value", value_reason({"relevance": 5, "value_band": "big"}))

    def test_percentage_without_comparison_does_not_qualify(self):
        self.assertIsNotNone(value_reason({"title": "Kids shoes 50% off", "discount_pct": 50}))

    def test_family_benefit_needs_conditions(self):
        self.assertIsNone(value_reason({"title": "Kids eat free", "description": "With an adult meal, under 12s only."}))
        self.assertIsNotNone(value_reason({"title": "Kids eat free"}))

    def test_family_benefit_classifies_without_gemini(self):
        deal = worker.normalise(raw("Kids go free with a paying adult"))
        worker.process_items([deal], [], [])
        self.assertEqual(deal["decision"], "kept")
        self.assertEqual(deal["display_group"], "Days Out & Family Fun")

    def test_free_offer_is_not_implausible(self):
        self.assertIsNone(worker.validate_deal(worker.normalise(raw("Kids go free with a paying adult", merchant_price="0"))))

    def test_redemption_query_retained_identity_removes_marketing_only(self):
        deal = worker.normalise(raw())
        self.assertIn("utm_source=feed", deal["link"])
        self.assertNotIn("utm_source", deal["dedupe_key"])
        self.assertIn("variant=blue", deal["dedupe_key"])
        self.assertIn("code=DAD", deal["dedupe_key"])

    def test_query_order_deduplicates_variants_remain_distinct(self):
        self.assertEqual(canonical_link("https://example.com/p?a=1&b=2"), canonical_link("https://example.com/p?b=2&a=1"))
        self.assertNotEqual(canonical_link("https://example.com/p?variant=red"), canonical_link("https://example.com/p?variant=blue"))

    def test_invalid_links(self):
        for link in ("httpwhatever", "javascript:alert(1)", "https://user:secret@example.com"):
            self.assertEqual(worker.validate_deal(worker.normalise(raw(link=link))), "bad_link")

    def test_known_dates_and_status(self):
        now = datetime.now(timezone.utc)
        for changes, reason in (({"expires_at": (now - timedelta(days=1)).isoformat()}, "expired"),
                                ({"starts_at": (now + timedelta(days=1)).isoformat()}, "not_started"),
                                ({"expires_at": "garbage"}, "invalid_offer_date"),
                                ({"source_status": "suspended"}, "source_unavailable")):
            self.assertEqual(worker.validate_deal(worker.normalise(raw(**changes))), reason)

    def test_save_outage_does_not_expire_unseen_offers(self):
        with patch.object(worker, "sb") as database:
            worker.save_live([], {}, [{"dedupe_key": "test", "decision": "rejected", "reason": "gemini_error"}])
        self.assertEqual(database.call_count, 1)
        self.assertIn("expires_at", database.call_args.kwargs["params"])
        self.assertNotIn("last_seen", database.call_args.kwargs["params"])

    def test_changed_weak_offer_is_removed_from_live_pool(self):
        with patch.object(worker, "sb") as database:
            worker.save_live([], {}, [{"dedupe_key": "test", "decision": "rejected", "reason": "unsupported_value: absent"}])
        self.assertEqual(database.call_args_list[0].kwargs["json"], {"status": "review"})

    def test_fmtc_retains_terms_code_expiry_and_sale_price(self):
        response = Mock(status_code=200)
        response.json.return_value = {"data": [{"id": 10, "label": "Baby cot", "sale_price": "150", "was_price": "200", "description": "Offer", "restrictions": "GB only, delivery £5", "code": "DAD", "status": "active", "end_date": "2026-12-01T00:00:00Z", "direct_link": "https://example.com/cot"}]}
        with patch.dict("os.environ", {"FMTC_API_TOKEN": "test"}), patch.object(adapters.requests, "get", return_value=response):
            status, records, _ = adapters.fetch_fmtc({"url": "config://fmtc"})
        deal = worker.normalise(records[0])
        self.assertEqual(status, "ok")
        self.assertEqual((deal["price"], deal["was_price"]), (150, 200))
        self.assertEqual(deal["dedupe_key"], "fmtc:10")
        self.assertIn("delivery £5", deal["description"])
        self.assertIn("DAD", deal["description"])
        self.assertEqual(deal["expires_at"], "2026-12-01T00:00:00Z")

    def test_awin_documented_fields(self):
        response = Mock(status_code=200)
        response.json.return_value = [{"promotionId": 42, "title": "Kids go free", "description": "Family tickets", "terms": "With a paying adult", "voucher": {"code": "DAD"}, "urlTracking": "https://track.example.com/?id=42", "endDate": "2026-12-01T00:00:00.000"}]
        with patch.dict("os.environ", {"AWIN_API_TOKEN": "test", "AWIN_PUBLISHER_ID": "1"}), patch.object(adapters.requests, "post", return_value=response) as request:
            _, records, _ = adapters.fetch_awin({"url": "config://awin"})
        self.assertEqual(request.call_args.kwargs["json"]["filters"]["regionCodes"], ["GB"])
        self.assertEqual(records[0]["identity"], "awin:42")
        self.assertIn("DAD", records[0]["description_raw"])
        self.assertIn("paying adult", records[0]["description_raw"])
        self.assertIn("id=42", records[0]["link"])


if __name__ == "__main__":
    unittest.main()


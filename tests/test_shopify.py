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

    def test_variant_identity_and_merchant_advertised_value(self):
        raw = s.rows(product(), self.url, self.shop)[0]
        deal = worker.normalise(raw)
        self.assertEqual(deal["price"], 9)
        self.assertIn("variant=2", deal["link"])
        self.assertEqual(deal["dedupe_key"], worker.normalise(raw)["dedupe_key"])
        self.assertEqual(deal["value_evidence_status"], "merchant_advertised")
        self.assertIsNone(value_reason(deal))
        self.assertEqual(deal["was_price"], 18)
        self.assertIn("not independently verified", raw["description_raw"])

    def test_sold_out_subscription_and_invalid_prices(self):
        self.assertEqual(s.rows(product(False), self.url, self.shop)[0]["source_status"], "unavailable")
        p = product(); p["variants"][0]["requires_selling_plan"] = True
        self.assertEqual(s.rows(p, self.url, self.shop)[0]["source_status"], "unavailable")
        for value in (True, -1, float("nan"), "900"):
            self.assertEqual(s.rows(product(price=value), self.url, self.shop), [])

    def test_age_size_is_evidence_but_adult_and_teen_sizes_are_not(self):
        for size, prefix in (("0-12 months", "Baby "), ("Navy / 0 - 3 M", "Baby "),
                             ("1-3 years", "Children's "), ("Adult / M", ""),
                             ("13-16 years", ""), ("120 cm", "")):
            p = product(); p["title"] = "Cosy hat"; p["variants"][0]["title"] = size
            title = s.rows(p, self.url, self.shop)[0]["title_raw"]
            self.assertEqual(title.startswith("Baby ") or title.startswith("Children's "), bool(prefix))

    def test_json_never_executes_and_requires_handle(self):
        text = '<script>window.product = ' + json.dumps(product()) + '; danger();</script>'
        self.assertEqual(s.product_json(text, "baby-hat")["id"], 1)
        self.assertIsNone(s.product_json(text, "wrong"))
        analytics = product(); analytics["variants"][0]["price"] = {"amount": 9, "currencyCode": "GBP"}
        mixed = '<script>' + json.dumps(analytics) + '</script>' + text
        self.assertEqual(s.product_json(mixed, "baby-hat")["variants"][0]["price"], 900)

    def test_reviewed_public_json_requires_same_page_identity_and_stock(self):
        shop = next(v for v in s.SHOPS.values() if v["name"] == "Snuz")
        url = "https://www.snuz.co.uk/products/baby-hat"
        metadata = '<script>' + json.dumps({"id": 1, "handle": "baby-hat"}) + '</script>'
        pages = {}
        with patch.object(s, "read", return_value=("ok", json.dumps(product()))) as read:
            self.assertEqual(s.load_product(metadata, url, shop, pages)["id"], 1)
            self.assertEqual(s.load_product(metadata, url, shop, pages)["id"], 1)
            read.assert_called_once_with(url + ".js", shop)
            self.assertIsNone(s.load_product(metadata.replace('"id": 1', '"id": 9'), url, shop, pages))
        unavailable = product(); del unavailable["variants"][0]["available"]
        with patch.object(s, "read", return_value=("ok", json.dumps(unavailable))):
            self.assertIsNone(s.load_product(metadata, url, shop))
        self.assertTrue(s.allowed(url + ".js", shop))
        self.assertFalse(s.allowed(url + ".js", self.shop))
        self.assertFalse(s.allowed(url + ".js?token=anything", shop))

    def test_reviewed_collection_skips_unmapped_products_before_fetch(self):
        feed, shop = next((k, v) for k, v in s.SHOPS.items() if v["name"] == "Cheeky Rascals")
        url = "https://www.cheekyrascals.co.uk/products/baby-hat"
        xml = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Pre-loved warmer</title><link href="' + url + '"/></entry></feed>'
        with patch.object(s, "read", return_value=("ok", xml)) as read:
            self.assertEqual(s.fetch_shopify({"url": feed})[:2], ("empty", []))
            read.assert_called_once_with(feed, shop)

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
        for p, expected in ((product(), None), (product(False), "source_unavailable"), (product(price=1000), "price_changed")):
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
            self.assertEqual(fresh["value_evidence_status"], "merchant_advertised")

    def test_description_uses_complete_product_then_same_product_schema(self):
        stub = product(); stub["description"] = "1"
        complete = product(); complete["description"] = "<p>Soft organic cotton for babies.</p>"
        text = '<script>' + json.dumps(stub) + '</script><script>' + json.dumps(complete) + '</script>'
        self.assertEqual(s.product_json(text, "baby-hat")["description"], "Soft organic cotton for babies.")
        schema = {"@type": "Product", "name": "Baby hat", "url": self.url, "description": "A warm fleece-lined hat for babies."}
        text = '<script>' + json.dumps(stub) + '</script><script type="application/ld+json">' + json.dumps(schema) + '</script>'
        self.assertEqual(s.product_json(text, "baby-hat")["description"], schema["description"])
        schema["url"] = self.url.replace("baby-hat", "adult-hat")
        text = '<script>' + json.dumps(stub) + '</script><script type="application/ld+json">' + json.dumps(schema) + '</script>'
        self.assertEqual(s.product_json(text, "baby-hat")["description"], "1")

    def test_structured_mapping_uses_active_canonical_identity(self):
        p = product(); p["type"] = "Hats"; p["title"] = "Hygge flower fable"
        raw = s.rows(p, self.url, self.shop)[0]; d = worker.normalise(raw)
        entries = worker.compile_items([{"id": 136, "active": "yes", "item_or_service": "Kids hats", "uk_terms": "kids hats", "display_group": "Kids' Clothes & Shoes", "tier": "B", "value_band": "low"}])
        worker.process_items([d], entries, [])
        self.assertEqual(d["decision"], "kept"); self.assertEqual(d["item_id"], 136)
        d = worker.normalise(raw); worker.process_items([d], [], [])
        self.assertEqual(d["decision"], "rejected")
        p["variants"][0]["title"] = "13-16 years"
        d = worker.normalise(s.rows(p, self.url, self.shop)[0])
        self.assertTrue(worker.validate_deal(d).startswith("outside_audience"))
        self.assertIsNone(d["taxonomy_item_label"])

    def test_specific_outerwear_and_unknown_types(self):
        p = product(); p.update(type="Outerwear", title="Splash Coat", description="Warm waterproof coat")
        self.assertEqual(s.taxonomy_label(p), "Kids raincoats")
        p.update(title="Quilted Cocoon Coat", description="Warm winter coat")
        self.assertEqual(s.taxonomy_label(p), "Kids winter coats")
        p["type"] = "Dungarees"
        self.assertIsNone(s.taxonomy_label(p))

    def test_missing_invalid_and_changed_compare_prices_still_reject(self):
        for comparison in (None, 0, 900, 800, True, "1800"):
            p = product(); p["variants"][0]["compare_at_price"] = comparison
            d = worker.normalise(s.rows(p, self.url, self.shop)[0])
            self.assertTrue(value_reason(d).startswith("unsupported_value"))
        d = worker.normalise(s.rows(product(), self.url, self.shop)[0])
        p = product(); p["variants"][0]["compare_at_price"] = 2000
        with patch.object(s, "read", return_value=("ok", '<script>' + json.dumps(p) + '</script>currency="GBP"')):
            self.assertEqual(verify_offer(d)[0], "comparison_unconfirmed")
        p = product(price=1790)
        self.assertTrue(value_reason(worker.normalise(s.rows(p, self.url, self.shop)[0])).startswith("weak_value"))

    def test_currency_is_not_inferred_from_a_stale_schema(self):
        self.assertFalse(s.gbp('Shopify.currency = {"active":"USD"}; "priceCurrency":"GBP"'))
        self.assertFalse(s.gbp('currency="USD"'))
        self.assertFalse(s.gbp('no currency'))
        self.assertTrue(s.gbp('Shopify.currency = {"active":"GBP"};'))

    def test_verification_snapshot_is_shared_only_within_one_run(self):
        d = worker.normalise(s.rows(product(), self.url, self.shop)[0])
        text = '<script>' + json.dumps(product()) + '</script>currency="GBP"'
        from deals_verification import verify_kept
        deals = [{**d, "decision": "kept", "classified_by": "quality-v1:rules"} for _ in range(2)]
        with patch.object(s, "read", return_value=("ok", text)) as read:
            verify_kept(deals, worker.reject)
            self.assertEqual(read.call_count, 1)
            self.assertTrue(all(x["classified_by"] == "quality-v1:source-page:merchant-advertised:rules" for x in deals))
            verify_kept([{**d, "decision": "kept", "classified_by": "quality-v1:rules"}], worker.reject)
            self.assertEqual(read.call_count, 2)

    def test_redirects_blocked_and_oversize_rejected(self):
        with patch.object(s.requests, "get") as get:
            response = get.return_value.__enter__.return_value
            response.status_code = 302
            self.assertEqual(s.read(self.url, self.shop)[0], "http_302")
            self.assertFalse(get.call_args.kwargs["allow_redirects"])
            response.status_code = 200
            response.iter_content.return_value = [b"x" * (s.MAX_BYTES + 1)]
            self.assertEqual(s.read(self.url, self.shop)[0], "oversize_page")

    def test_transient_server_error_recovers_once_without_unbounded_retries(self):
        with patch.object(s.requests, "get") as get, patch.object(s.time, "sleep"):
            response = get.return_value.__enter__.return_value
            response.status_code = 500
            self.assertEqual(s.read(self.url, self.shop), ("http_500", ""))
            self.assertEqual(get.call_count, 2)
            get.reset_mock()
            type(response).status_code = property(lambda self: next(statuses))
            statuses = iter([500, 200, 200])
            response.iter_content.return_value = [b"public merchant page"]
            self.assertEqual(s.read(self.url, self.shop), ("ok", "public merchant page"))
            self.assertEqual(get.call_count, 2)

    def test_reviewed_new_store_mapping_requires_product_evidence(self):
        shop = s.SHOPS['https://www.babipur.co.uk/collections/all-sale-at-babipur.atom']
        p = product(); p.update(title='Frugi Navigator Backpack - Snow', description="A children's backpack for school.")
        p['variants'][0]['title'] = 'Default Title'
        d = worker.normalise(s.rows(p, 'https://www.babipur.co.uk/products/backpack', shop)[0])
        entries = worker.compile_items([{'id':166,'active':True,'item_or_service':'Backpacks','uk_terms':'backpacks',
            'display_group':'School & Learning','tier':'B','value_band':'mid','needs_child_evidence':True}])
        self.assertEqual(worker.layer1_match(d, entries)[1]['item_id'], 166)
        self.assertIn('school', worker.layer1_match(d, entries)[1]['term'])
        d['shopify_audience_evidence'] = 'Invented children evidence'
        d['description'] = 'General-purpose bag.'
        self.assertEqual(worker.layer1_match(d, entries), (None,None))
        p.update(title='Replacement Backpack Strap', description='For children at school')
        d = worker.normalise(s.rows(p, self.url, shop)[0])
        self.assertIsNone(d['taxonomy_item_label'])
        self.assertEqual(worker.layer1_match(d, entries), (None,None))

    def test_inherent_baby_goods_do_not_need_clothing_size(self):
        examples = [('https://www.babipur.co.uk/collections/all-sale-at-babipur.atom','GroVia AIO Petal','Cloth diapers'),
                    ('https://www.cheekyrascals.co.uk/collections/sale.atom','Baby Brezza Food Maker Deluxe','Baby food maker'),
                    ('https://www.snuz.co.uk/collections/outlet.atom','SnuzFino Cot Bed - Slate','Cot bed'),
                    ('https://babygo.uk/collections/baby-proofing.atom','BABYGO Baby Gate For Stairs','Baby gate')]
        for feed,title,label in examples:
            p=product();p.update(title=title,description='');p['variants'][0]['title']='Default Title'
            raw=s.rows(p,'https://'+s.SHOPS[feed]['host']+'/products/item',s.SHOPS[feed])[0]
            self.assertEqual(raw['taxonomy_item_label'],label)
        snuz=s.SHOPS[examples[2][0]]
        for title in ('SnuzFino Cot Bed Conversion Rail','SnuzFino Cot Bed Bundle','SnuzFino Cot Bed Replacement Mattress'):
            p=product();p['title']=title
            self.assertIsNone(s.taxonomy_label(p,snuz))

    def test_verification_budget_shares_sources_and_items(self):
        from deals_verification import verify_kept
        rows=[{'source_id':1,'item_id':118,'link':str(i),'decision':'kept','classified_by':'quality-v1:rules'} for i in range(4)]
        rows += [{'source_id':1,'item_id':130,'link':'coat','decision':'kept','classified_by':'quality-v1:rules'},
                 {'source_id':2,'item_id':90,'link':'gate','decision':'kept','classified_by':'quality-v1:rules'}]
        with patch('deals_verification.verify_offer',return_value=(None,'source-page')) as verify:
            verify_kept(rows,worker.reject,max_checks=3)
        self.assertEqual([call.args[0]['link'] for call in verify.call_args_list],['0','gate','coat'])
        self.assertEqual(sum(r['decision']=='kept' for r in rows),3)


if __name__ == "__main__":
    unittest.main()

import copy
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import deals_matalan as m
import deals_worker as worker
from deals_verification import verify_offer


def wrap(v):
    return [0, {k: wrap(x) for k, x in v.items()}] if isinstance(v, dict) else [1, [wrap(x) for x in v]] if isinstance(v, list) else [0, v]


def fixture():
    v = {"sku": int(m.VARIANT), "title": m.TITLE, "inStock": True,
         "choices": [{"optionKey": "Size", "key": "Age 4 Years"}, {"optionKey": "Colour", "key": "Black"}],
         "price": {"price": {"amount": "7.20", "currency": "GBP"}, "rrp": {"amount": "9", "currency": "GBP"}}}
    ld = {"@type": "ProductGroup", "productGroupID": "14894526", "hasVariant": [{"sku": m.VARIANT, "size": "Age 4 Years", "color": "Black", "offers": {"sku": m.VARIANT, "url": m.OFFER_URL, "price": 7.2, "priceCurrency": "GBP", "availability": "https://schema.org/InStock"}}]}
    return v, ld


def html(v, ld):
    import html as h
    return '<astro-island component-url="/ssr-assets/MarketedSpecialOffer.hash.js" props="' + h.escape(json.dumps({"activeVariantData": wrap(v)}), quote=True) + '"></astro-island><script type="application/ld+json">' + json.dumps(ld) + '</script>'


class MatalanTests(unittest.TestCase):
    def setUp(self):
        clock = patch.object(m, "datetime", wraps=datetime)
        clock.start().now.return_value = datetime(2026, 10, 17, tzinfo=timezone.utc)
        self.addCleanup(clock.stop)

    def test_exact_identity_prices_and_independent_stock(self):
        v, ld = fixture()
        self.assertEqual(tuple(map(float, m.parse_product(html(v, ld)))), (7.2, 9))
        for mutation in [lambda a,b:a.update(inStock=False), lambda a,b:a.update(sku=123),
                         lambda a,b:a["price"]["price"].update(currency="EUR"),
                         lambda a,b:b["hasVariant"][0]["offers"].update(price=8),
                         lambda a,b:b["hasVariant"][0]["offers"].update(availability="https://schema.org/OutOfStock"),
                         lambda a,b:a["choices"][0].update(key="Age 6 Years"),
                         lambda a,b:a["price"].pop("rrp"),
                         lambda a,b:b["hasVariant"][0]["offers"].update(url=m.PRODUCT_URL)]:
            a,b = copy.deepcopy(v),copy.deepcopy(ld); mutation(a,b)
            self.assertIsNone(m.parse_product(html(a,b)))
        self.assertIsNone(m.parse_product(html(v,ld) * 2))
        self.assertIsNone(m.parse_product('<script>doSomething()</script>'))

    def test_bad_money_is_never_saving(self):
        for value in [True, None, [], {}, "nan", "Infinity", -1, 0, "7.201"]:
            self.assertIsNone(m.money(value))

    def test_bounded_http_no_redirect_or_arbitrary_url(self):
        with patch.object(m.requests, "get") as get:
            self.assertEqual(m.read(m.OFFER_URL + "&evil=1")[0], "unsupported_url")
            get.assert_not_called()
            response = MagicMock(status_code=302)
            get.return_value.__enter__.return_value = response
            self.assertEqual(m.read(m.OFFER_URL)[0], "http_302")
            self.assertFalse(get.call_args.kwargs["allow_redirects"])
            response.status_code=200; response.headers={"Content-Type":"text/html"}
            response.iter_content.return_value=[b'x'*(m.MAX_BYTES+1)]
            self.assertEqual(m.read(m.OFFER_URL)[0], "oversize_page")

    def pages(self, url):
        if url == m.SOURCE_URL:return "ok", '<a href="'+m.PRODUCT_URL+'">Uniform</a>'
        if url == m.OFFER_URL:return "ok", html(*fixture())
        if url == m.DELIVERY_URL:return "ok", 'Standard Home Delivery (£3.99) Orders Over £49.99 Standard Click & Collect (£0.99 or Free for Orders Over £19.99)'
        return "ok", '20% Off (Almost) Everything - Online Only 19.10.26 at Midnight online and via the APP only Cannot be used in conjunction'

    def test_normal_pipeline_value_and_exact_refetch(self):
        with patch.object(m, "read", side_effect=self.pages):
            status, raw, _ = m.fetch_matalan({"url":m.SOURCE_URL})
            self.assertEqual(status,"ok")
            d=worker.normalise(raw[0])
            self.assertIsNone(worker.validate_deal(d))
            self.assertEqual(d["price"],7.2)
            self.assertEqual(d["was_price"],9)
            self.assertIn("£11.19",d["description"])
            self.assertEqual(verify_offer(d),(None,"source-page"))
            d["price"]=7
            self.assertEqual(verify_offer(d)[0],"matalan_evidence_changed")

    def test_changed_terms_and_delivery_fail_closed(self):
        for changed, expected in [(m.TERMS_URL,"terms_changed"),(m.DELIVERY_URL,"delivery_changed"),(m.SOURCE_URL,"product_not_listed")]:
            with patch.object(m,"read",side_effect=lambda u: ("ok","Changed") if u==changed else self.pages(u)):
                self.assertEqual(m.fetch_matalan({"url":m.SOURCE_URL})[0],expected)
        with patch.object(m,"read",return_value=("http_503","")):
            self.assertEqual(m.fetch_matalan({"url":m.SOURCE_URL})[1],[])

    def test_review_cutoff_stops_even_if_badges_remain(self):
        with patch.object(m,"VALID_UNTIL","2000-01-01T00:00:00Z"), patch.object(m,"read") as read:
            self.assertEqual(m.fetch_matalan({"url":m.SOURCE_URL})[0],"review_expired")
            read.assert_not_called()


if __name__ == '__main__':unittest.main()

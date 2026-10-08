import json
import unittest
from unittest.mock import Mock, patch
import deals_worker as w
import deals_worker_db as db
from deals_quality import prices, value_reason
from deals_direct_sources import fetch_direct, RECIPES
from deals_halfords import products, offer, verify_halfords
from deals_source_adapters import _raw


def item(id, name, terms, **changes):
    return dict(id=id, item_or_service=name, uk_terms=terms, active=True, display_group='Baby & Maternity Essentials', tier='A', value_band='mid', deal_type='product', needs_child_evidence=False, **changes)


class EconomicsTests(unittest.TestCase):
    def test_conflicting_current_price_retailer_goes_to_review(self):
        d=w.normalise(_raw(title='School dress',price='7',merchant='Ocado',description='£7 at M&S. Was £12.',link='https://example.com/x'))
        self.assertTrue(w.validate_deal(d).startswith('merchant_conflict'))

    def test_no_paid_call_even_if_key_and_classifier_are_available(self):
        deal = w.normalise(_raw(title='Children mystery product now £20 was £30', link='https://example.com/x'))
        classifier = Mock()
        with patch.object(w, 'ENABLE_PAID_AI', False):
            stats = w.process_items([deal], [], [], classifier)
        classifier.assert_not_called()
        self.assertEqual(stats['tokens_in'] + stats['tokens_out'], 0)
        self.assertTrue(deal['reason'].startswith('unmapped_item'))

    def test_specific_canonical_item_wins(self):
        entries = w.compile_items([item(1,'Nappies','nappy; nappies'),item(11,'Bin refills','nappy bin refills')])
        d = w.normalise(_raw(title='Nappy bin refills now £20 was £30',link='https://example.com/x'))
        w.process_items([d], entries, [])
        self.assertEqual(d['item_id'],11)

    def test_child_evidence_is_required_for_generic_bikes(self):
        row = item(454,'Bicycle','bike')
        row['needs_child_evidence']=True
        entries=w.compile_items([row])
        for title, expected in [('Adult bike now £150 was £200','rejected'),('Junior bike now £150 was £200','kept')]:
            d=w.normalise(_raw(title=title,link='https://example.com/x'))
            w.process_items([d],entries,[])
            self.assertEqual(d['decision'],expected)

    def test_different_example_prices_do_not_create_fake_savings(self):
        self.assertEqual(prices({'merchant_price':'2.55'},'15% off school uniform','£2.55 polo shirts. School shirts £3.40 Was £4.00'),(2.55,None,None))
        self.assertEqual(prices({'merchant_price':'7'},'School dress','£7 at M&S, down from £12. Was £12.'),(7,12,41.7))

    def test_two_digit_child_age_benefit(self):
        self.assertIsNone(value_reason({'title':'Kids eat free breakfast','description':'Children under 16 with a full adult breakfast'}))

    def test_package_and_tuition_terms_are_required(self):
        d={'title':'Family holiday now £900 was £1200','description':'A family package deal','matched_item':'Family package holidays','price':900,'was_price':1200,'discount_pct':25}
        self.assertTrue(value_reason(d).startswith('missing_applicability'))
        d['description']='Depart 2027-04-05, 2 adults and 2 children. Mandatory fees included, transfers and baggage included.'
        self.assertIsNone(value_reason(d))
        d.update(matched_item='Online tutoring',description='Maths, aged 8, online, 4 sessions of 60 minutes. One-off payment; no subscription.')
        self.assertIsNone(value_reason(d))

    def test_transient_failure_keeps_source_active_and_verified_time_unchanged(self):
        with patch.object(w,'sb') as query:
            w.update_source_health({'id':1,'consecutive_failures':9},'http_503',{'verified':0})
        values=query.call_args.kwargs['json']
        self.assertNotIn('active',values)
        self.assertNotIn('last_verified_at',values)
        self.assertNotIn('last_success_at',values)

    def test_taxonomy_paginates_beyond_api_default(self):
        with patch.object(w,'sb',side_effect=[[{'id':i} for i in range(500)],[{'id':i} for i in range(500,1000)],[{'id':1000}]]) as query:
            rows=db.read_all('parent_discount_items')
        self.assertEqual(len(rows),1001)
        self.assertEqual(query.call_args.kwargs['params']['offset'],1000)

    def test_direct_offer_fails_when_terms_change(self):
        url=next(iter(RECIPES))
        with patch('deals_direct_sources.page_text',return_value=('ok','Kids eat free; ask in store')):
            self.assertEqual(fetch_direct({'url':url})[0],'terms_changed')

    def test_terms_page_without_advertised_campaign_cannot_publish(self):
        url='https://www.pizzaexpress.com/terms-and-conditions/kids-eat-free'
        text='One Piccolo meal with purchase of any full-price adult main. 12 years or below. £15 minimum spend. One code is required. Not valid for Collection or Delivery.'
        with patch('deals_direct_sources.page_text',side_effect=[('ok',text),('ok','Our latest lunch menu')]):
            self.assertEqual(fetch_direct({'url':url})[0],'campaign_unconfirmed')

    def test_halfords_current_product_prices_must_match_discovered_offer(self):
        p={'id':'123456','productName':'Kids bike','price':{'sales':{'value':80,'currency':'GBP'},'list':{'value':100,'currency':'GBP'}},'available':True,'availability':{'isInStock':True}}
        text='<script>'+json.dumps({'product':p})+'</script>'
        self.assertEqual(offer(products(text)[0]),(80,100))
        d={'link':'https://www.halfords.com/bikes/kids-bikes/kids-bike-123456.html','merchant_product_id':'123456','price':75,'was_price':100}
        with patch('deals_halfords.read_page',return_value=('ok',text)):
            self.assertEqual(verify_halfords(d)[0],'verification_price_changed')
        p['availability']['isInStock']=False
        self.assertIsNone(offer(p))

    def test_verification_budget_never_marks_unchecked_rows_fresh(self):
        from deals_verification import verify_kept
        rows=[{'decision':'kept','classified_by':'quality-v1:rules'} for _ in range(2)]
        with patch('deals_verification.verify_offer',return_value=(None,'source-page')) as check:
            verify_kept(rows,w.reject,max_checks=1)
        self.assertEqual(check.call_count,1)
        self.assertEqual(rows[1]['decision'],'rejected')
        self.assertEqual(rows[1]['classified_by'],'quality-v1:rules')

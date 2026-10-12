import datetime as dt
import unittest
from session_proposals import parse_spydus,parse_mini_athletics,parse_stay_and_play

class SessionProposalTests(unittest.TestCase):
    def card(self,token='123',date='14 Oct 2026'):
        return '<div class="card-record-body"><h3 class="card-title"><a href="/FULL/'+token+'/164914126,1">Storytime</a></h3><div class="recdetails"><span>'+date+' - 10:30 AM to 11:00 AM</span><span>Tring Library</span></div><div class="summary">For pre-school children. Term time only. Free.</div></div>'
    def test_library_session_identity_survives_search_token_changes_and_preserves_occurrence(self):
        a,_=parse_spydus(self.card(),'https://herts.spydus.co.uk/search',dt.date(2026,10,12))
        b,_=parse_spydus(self.card('changed'),'https://herts.spydus.co.uk/search',dt.date(2026,10,12))
        self.assertEqual(a[0]['proposal_key'],b[0]['proposal_key'])
        self.assertEqual(a[0]['dates'],'2026-10-14')
        self.assertIn('Term time only',a[0]['notes'])
        old,_=parse_spydus(self.card(date='9 Oct 2026'),'https://herts.spydus.co.uk/search',dt.date(2026,10,12))
        self.assertEqual(old,[])
    def test_pagination_hidden_labels_are_observed_and_shells_fail(self):
        _,next_pages=parse_spydus(self.card()+'<a href="/page2" aria-label="Next">Next<span> page of search results</span></a>','https://herts.spydus.co.uk/search',dt.date(2026,10,12))
        self.assertEqual(next_pages,['https://herts.spydus.co.uk/page2'])
        with self.assertRaises(ValueError):parse_spydus('<div>Loading</div>','https://herts.spydus.co.uk/search',dt.date(2026,10,12))
    def test_rolling_classes_keep_half_year_ages_and_do_not_invent_dates(self):
        row='<div class="contained"><h2>Centre</h2><p>Centre CB2 9HB</p><table><tbody><tr><td data-title="Class">Little Athletes 3½ - 5 Years</td><td data-title="Time">Saturday 9:45am - 10:30am</td><td data-title="Dates">Rolling</td><td data-title="Spaces">Available</td><td data-title="Book now"><a href="/book/1/">Book</a></td></tr></tbody></table></div>'
        items,_=parse_mini_athletics(row,'https://www.miniathletics.com/summary/',dt.date(2026,10,12))
        self.assertEqual(items[0]['ages'],'3½ - 5 Years');self.assertEqual(items[0]['dates'],'')
        items,errors=parse_mini_athletics(row.replace('Available','Full'),'https://www.miniathletics.com/summary/',dt.date(2026,10,12))
        self.assertEqual(items,[]);self.assertEqual(len(errors),1)
    def test_incomplete_centre_timetable_cannot_claim_five_sessions(self):
        with self.assertRaises(ValueError):parse_stay_and_play('<div class="prose"><p>Tuesday: 10 - 11.30am, Fawcett Child and Family Zone</p></div>','https://haycambridge.co.uk/activities/child-family-centres-stay-and-play/')

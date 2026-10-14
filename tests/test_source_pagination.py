import unittest
from unittest.mock import Mock
from source_pagination import collect


class PaginationTests(unittest.TestCase):
    root = 'https://cardiffhubs.co.uk/events/'
    second = 'https://cardiffhubs.co.uk/events/page/2'

    def test_observed_pages_cycle_external_and_login_are_bounded(self):
        fetch = Mock(side_effect=['<a href="/events/page/2">Next</a>'
                                 '<a href="https://evil.test/events/page/3">3</a>'
                                 '<a href="https://user:pass@cardiffhubs.co.uk/events/page/4">4</a>',
                                 '<a href="/events/page/2">2</a><p>Last</p>'])
        docs = collect({'url': self.root}, fetch, lambda _: (True, ''), lambda: None)
        self.assertEqual([url for url, _ in docs], [self.root, self.second])
        self.assertEqual(fetch.call_count, 2)

    def test_budget_and_robots_fail_instead_of_partial_success(self):
        for cap, robots in [(1, lambda _: (True, '')),
                            (2, lambda url: (url == self.root, 'disallowed'))]:
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                collect({'url': self.root, 'listing_page_limit': cap},
                        lambda _: '<a href="/events/page/2">Next</a>', robots, lambda: None)

    def test_other_hosts_not_implicitly_qualified(self):
        with self.assertRaises(ValueError):
            collect({'url': 'https://example.org/events/'}, Mock(), Mock(), Mock())

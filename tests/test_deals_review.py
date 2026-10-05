import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("review", Path(__file__).parent.parent / "scripts/check-deals-review.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewGateTests(unittest.TestCase):
    def labels(self, **changes):
        return {**{field: "yes" for field in review.REQUIRED}, **changes}

    def test_empty_and_unlabelled_reviews_fail(self):
        self.assertFalse(review.measure([])[0])
        self.assertFalse(review.measure([{}])[0])

    def test_top_twenty_threshold(self):
        rows = [self.labels() for _ in range(18)] + [self.labels(human_valuable="no") for _ in range(2)]
        self.assertTrue(review.measure(rows, top=True)[0])
        rows[0]["human_relevant"] = "no"
        self.assertFalse(review.measure(rows, top=True)[0])

    def test_one_expired_offer_fails_even_with_ninety_nine_useful_offers(self):
        rows = [self.labels() for _ in range(100)]
        rows[0]["human_not_expired"] = "no"
        self.assertFalse(review.measure(rows)[0])

    def test_one_unsupported_claim_fails(self):
        self.assertFalse(review.measure([self.labels(human_savings_supported="no")])[0])


"""Assess completed human labels; blank labels are never counted as approval."""
import csv
import sys

FIELDS = ("human_relevant", "human_valuable", "human_terms_clear", "human_link_works")
REQUIRED = FIELDS + ("human_not_expired", "human_savings_supported")


def measure(rows, top=False):
    if not rows:
        return False, "No published offers: quality target cannot be assessed."
    if any(str(row.get(field, "")).lower() not in {"yes", "no"} for row in rows for field in REQUIRED):
        return False, "Review incomplete: label every field yes/no."
    if any(row[field].lower() != "yes" for row in rows for field in ("human_not_expired", "human_savings_supported")):
        return False, "Release fails: expired offer or unsupported savings claim reported."
    good = sum(all(row[field].lower() == "yes" for field in FIELDS) for row in rows)
    target = 0.9
    passed = good / len(rows) >= target
    return passed, f"{good}/{len(rows)} useful offers ({good / len(rows):.0%}); target {'18/20' if top and len(rows) == 20 else '90%'}{' met' if passed else ' missed'}."


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/check-deals-review.py published-review.csv top-20-review.csv")
    outcomes = []
    for index, filename in enumerate(sys.argv[1:]):
        with open(filename, newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        passed, result = measure(rows, top=index == 1)
        print(result)
        outcomes.append(passed)
    raise SystemExit(0 if all(outcomes) else 1)


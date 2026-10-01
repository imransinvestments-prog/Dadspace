#!/usr/bin/env python3
"""Run the Dadspace deals worker using Supabase tables for matching data.

This is a compatibility entry point around deals_worker.py.  The core worker
still owns all deal fetching/classification logic; this module replaces its
legacy CSV loader with reads from:

- public.parent_discount_items
- public.parent_deal_exclusions

It also normalises PostgreSQL booleans to the legacy yes/no shape expected by
the existing matching compiler.  If parent_deal_exclusions does not have a
`mode` column, exclusions default to `soft`, preserving child-specific deals
unless an exclusion is explicitly marked hard.
"""

import sys

import deals_worker as worker


ITEMS_TABLE = "parent_discount_items"
EXCLUSIONS_TABLE = "parent_deal_exclusions"


def _truthy(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def load_items_from_supabase():
    rows = worker.sb(
        "GET",
        ITEMS_TABLE,
        params={"select": "*", "order": "id"},
    ) or []

    # compile_items() predates the DB tables and expects CSV-style yes/no text.
    for row in rows:
        row["active"] = "yes" if _truthy(row.get("active", True)) else "no"
        row["uk_terms"] = row.get("uk_terms") or ""
        row["display_group"] = row.get("display_group") or ""
        row["tier"] = row.get("tier") or ""
        row["value_band"] = row.get("value_band") or "low"
        row["item_or_service"] = row.get("item_or_service") or ""
    return rows


def load_exclusions_from_supabase():
    rows = worker.sb(
        "GET",
        EXCLUSIONS_TABLE,
        params={"select": "*", "order": "id"},
    ) or []

    # The original exclusion CSV included mode.  The current DB table may only
    # contain term/reason, so default missing modes to soft.
    for row in rows:
        row["term"] = row.get("term") or ""
        row["reason"] = row.get("reason") or ""
        row["mode"] = (row.get("mode") or "soft").strip().lower()
    return rows


def load_database_list(path):
    """Drop-in replacement for deals_worker.load_csv()."""
    if path == worker.ITEMS_CSV:
        return load_items_from_supabase()
    if path == worker.EXCLUSIONS_CSV:
        return load_exclusions_from_supabase()
    raise RuntimeError(f"Unexpected legacy list path: {path}")


def main():
    # Replace the legacy file-backed list loader before self_test/run is called.
    worker.load_csv = load_database_list

    if "--self-test" in sys.argv:
        return 0 if worker.self_test() else 1
    return worker.run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as crash:  # keep the original worker's crash logging behaviour
        import traceback

        traceback.print_exc()
        if worker._SB_URL and worker._SB_KEY:
            worker.log_run(
                0,
                {
                    "status": "crashed",
                    "error": str(crash)[:300],
                    "model": worker.GEMINI_MODEL,
                    "total_tokens": worker.STATS["tokens_in"] + worker.STATS["tokens_out"],
                },
            )
        sys.exit(1)

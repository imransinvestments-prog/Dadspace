"""Validate Awin before enabling its existing source; never print credentials."""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import deals_worker as worker
from deals_source_adapters import fetch_awin


def main(activate=False):
    if not (worker._SB_URL and worker._SB_KEY):
        print("Supabase configuration missing")
        return 1
    sources = worker.sb("GET", "deal_sources", params={"source_type": "eq.awin", "select": "id,url,active"}) or []
    if len(sources) != 1:
        print("Expected exactly one Awin source. Review deal_sources_api_sources.sql before setup.")
        return 1
    status, offers, info = fetch_awin(sources[0])
    print(f"Awin validation: {status}; {len(offers)} source-listed offers. {info}")
    if status not in {"ok", "empty"}:
        return 1
    if not activate:
        print("Read-only check complete; no source or deals changed.")
        return 0
    worker.sb("PATCH", "deal_sources", params={"id": f"eq.{sources[0]['id']}", "source_type": "eq.awin"},
              json={"active": True}, headers={"Prefer": "return=minimal"})
    verified = worker.sb("GET", "deal_sources", params={"id": f"eq.{sources[0]['id']}", "select": "active"}) or []
    if len(verified) != 1 or verified[0].get("active") is not True:
        print("Activation could not be confirmed")
        return 1
    print("Awin source activation confirmed. Collection still applies all relevance/value gates.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    try:
        sys.exit(main(args.activate))
    except Exception:
        print("Awin setup failed; check database access and source configuration. Credentials were not logged.")
        sys.exit(1)

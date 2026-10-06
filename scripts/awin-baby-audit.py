"""Read-only AWIN baby-programme/offer trial. No database or membership writes."""
import json
import os
import pathlib
import re
import sys
import requests

BABY = re.compile(r"\b(bab(?:y|ies)|infant|newborn|napp(?:y|ies)|diaper|pushchair|pram|stroller|car seat|breastfeed|nursery furniture|maternity)\b", re.I)

def main():
    token = os.getenv("AWIN_API_TOKEN", "").strip()
    publisher = os.getenv("AWIN_PUBLISHER_ID", "").strip()
    if not token or not publisher.isascii() or not publisher.isdecimal():
        raise RuntimeError("AWIN credentials missing or publisher ID invalid")
    session = requests.Session()
    session.headers.update({"Authorization": "Bearer " + token, "Accept": "application/json"})
    root = "https://api.awin.com"
    def request(method, path, **kwargs):
        response = session.request(method, root + path, timeout=(10, 45), allow_redirects=False, **kwargs)
        if response.status_code != 200:
            raise RuntimeError("AWIN HTTP " + str(response.status_code))
        return response.json()
    def programmes(relationship=None):
        params = {"countryCode": "GB"}
        if relationship:
            params["relationship"] = relationship
        payload = request("GET", f"/publishers/{publisher}/programmes", params=params)
        if not isinstance(payload, list):
            raise RuntimeError("Unexpected programme response shape")
        return payload
    joined = programmes("joined")
    pending = programmes("pending")
    all_programmes = programmes()
    joined_ids = {p["id"] for p in joined}
    pending_ids = {p["id"] for p in pending}
    matches = []
    for p in all_programmes:
        if BABY.search(str(p.get("name", "")) + " " + str(p.get("description", ""))):
            matches.append({k: p.get(k) for k in ("id", "name", "description", "primarySector", "displayUrl", "status")})
            matches[-1]["membership"] = "joined" if p["id"] in joined_ids else "pending" if p["id"] in pending_ids else "not_joined_or_other"
    def offers(membership, ids=None):
        filters = {"membership": membership, "regionCodes": ["GB"], "status": "active", "type": "all"}
        if ids is not None:
            if not ids:
                return []
            filters["advertiserIds"] = ids
        result, signatures = [], set()
        for page in range(1, 21):
            payload = request("POST", f"/publisher/{publisher}/promotions",
                              json={"filters": filters, "pagination": {"page": page, "pageSize": 200}})
            items = payload if isinstance(payload, list) else next((payload[k] for k in ("offers", "promotions", "data", "results") if isinstance(payload.get(k), list)), None) if isinstance(payload, dict) else None
            if items is None:
                raise RuntimeError("Unexpected promotions response shape")
            signature = json.dumps(items, sort_keys=True)
            if items and signature in signatures:
                raise RuntimeError("Repeated promotions page; refusing partial report")
            signatures.add(signature)
            result.extend(items)
            if len(items) < 200:
                return result
        raise RuntimeError("Promotions safety limit; refusing partial report")
    joined_offers = offers("joined")
    baby_offers = offers("all", [p["id"] for p in matches])
    report = {"joined_programmes": len(joined), "pending_programmes": len(pending),
              "uk_programmes": len(all_programmes), "baby_programmes": matches,
              "joined_active_uk_offers": len(joined_offers),
              "baby_advertiser_active_uk_offers": baby_offers,
              "baby_specific_joined_offers": [o for o in joined_offers if BABY.search(str(o.get("title", "")) + " " + str(o.get("description", "")))],
              "note": "Discovery only. Broad store promotions are not necessarily baby-specific or valuable. No account memberships or database rows changed."}
    pathlib.Path("review").mkdir(exist_ok=True)
    pathlib.Path("review/awin-baby-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"UK programmes: {len(all_programmes)}; joined: {len(joined)}; pending: {len(pending)}; baby-related: {len(matches)}")
    print(f"Joined active UK offers: {len(joined_offers)}; baby-advertiser active UK offers: {len(baby_offers)}")
    for p in matches:
        print(f"Programme {p['id']}: {p['name']} [{p['membership']}]")
    for o in baby_offers[:25]:
        a = o.get("advertiser") or {}
        print(f"Offer {o.get('promotionId')}: {o.get('title')} | {a.get('name')} | joined={a.get('joined')}")
    print(report["note"])

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc) if isinstance(exc, RuntimeError) else "AWIN audit failed; no credentials logged")
        sys.exit(1)

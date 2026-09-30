import requests
import xml.etree.ElementTree as ET

URLS = [
    "https://www.hotukdeals.com/rss/tag/car-seat",
    "https://www.hotukdeals.com/rss/tag/car-seats",
    "https://www.hotukdeals.com/rss/tag/pushchair",
    "https://www.hotukdeals.com/rss/tag/pram",
    "https://www.hotukdeals.com/rss/tag/cot",
    "https://www.hotukdeals.com/rss/tag/baby",
    "https://www.hotukdeals.com/rss/search?q=car+seat",
    "https://www.hotukdeals.com/rss/search?q=pushchair",
    "https://www.hotukdeals.com/rss/group/baby-kids",
    "https://www.hotukdeals.com/rss/baby-kids",
]
HEADERS = {"User-Agent": "DadspaceFeedCheck/0.1"}

for url in URLS:
    print("=" * 60)
    print("Testing:", url)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
    except Exception as e:
        print("FAILED to connect:", e)
        continue
    print("Status:", r.status_code)
    if r.status_code != 200:
        continue
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        print("Not valid XML (probably a web page, not a feed)")
        continue
    items = root.findall(".//item")
    print("Items found:", len(items))
    for it in items[:5]:
        print("-", (it.findtext("title") or "").strip())
    cats = sorted({(it.findtext("category") or "").strip() for it in items})
    print("Categories seen:", cats)

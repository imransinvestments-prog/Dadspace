import requests
import xml.etree.ElementTree as ET

URLS = [
    "https://www.hotukdeals.com/rss/new",
    "https://www.hotukdeals.com/rss/hot",
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
    print("Content-Type:", r.headers.get("Content-Type"))
    if r.status_code != 200:
        print("Response starts:", r.text[:200].replace("\n", " "))
        continue
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        print("Not valid XML:", e)
        print("Response starts:", r.text[:200].replace("\n", " "))
        continue
    items = root.findall(".//item")
    print("Items found:", len(items))
    for it in items[:5]:
        print("-", (it.findtext("title") or "").strip())
    if items:
        print("Fields in first item:", [child.tag for child in items[0]])

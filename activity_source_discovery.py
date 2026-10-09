"""Bounded detail discovery for explicitly reviewed library/museum listings.

The source registry remains authoritative. No venue homepage is auto-activated.
Only source_adapter=venue_listing_details opts into this additional fetching.
"""
import os
import re
from urllib.parse import urljoin, urlparse, urldefrag

from bs4 import BeautifulSoup

DETAIL_SIGNAL = re.compile(r"\b(?:event|events|what.?s on|story.?time|rhyme.?time|workshop|family|families|children|lego|bookbug)\b", re.I)


def listing_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for element in soup.select('nav, header, footer, [role="navigation"], .menu, .navigation, .mega-menu'):
        element.decompose()
    root = soup.find("main") or soup.find(id="main-content") or soup
    return str(root)


def detail_urls(html, page_url, limit=4):
    """Keep source order; reject navigation, duplicate, private and external URLs."""
    origin = urlparse(page_url)
    urls = []
    soup = BeautifulSoup(listing_html(html), "html.parser")
    root = soup.find("main") or soup
    for link in root.find_all("a", href=True):
        if link.find_parent(["nav", "header", "footer"]):
            continue
        href = link["href"]
        url = urldefrag(urljoin(page_url, href))[0]
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or parsed.hostname != origin.hostname:
            continue
        if parsed.username or parsed.password or url == urldefrag(page_url)[0] or url in urls:
            continue
        if re.search(r"\.(?:pdf|jpg|png|zip|ics)$", parsed.path, re.I):
            continue
        if not DETAIL_SIGNAL.search(link.get_text(" ", strip=True) + " " + parsed.path):
            continue
        if re.search(r"/(?:login|account|search|privacy|contact|donate)(?:/|$)", parsed.path, re.I):
            continue
        urls.append(url)
        if len(urls) >= limit:
            break
    return urls


def fetch_listing_documents(source, fetch, robots, pause):
    """A partial discovery failure is a failed source, never a fresh empty feed."""
    page_url = source["url"]
    documents = [(page_url, listing_html(fetch(page_url)))]
    limit = min(8, max(0, int(os.environ.get("ACTIVITY_DETAIL_PAGES", "4"))))
    for url in detail_urls(documents[0][1], page_url, limit) if limit else []:
        allowed, reason = robots(url)
        if not allowed:
            raise RuntimeError("Detail page blocked by robots: " + reason)
        pause()
        documents.append((url, listing_html(fetch(url))))
    return documents

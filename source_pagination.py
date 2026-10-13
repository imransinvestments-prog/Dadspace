"""Follow observed Cardiff listing pages within an explicit source budget."""
import re
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup


def collect(source, fetch, robots, pause):
    root = source['url']
    origin = urlparse(root)
    if origin.hostname != 'cardiffhubs.co.uk' or origin.path.rstrip('/') != '/events':
        raise ValueError('Unqualified paginated source')
    cap = int(source.get('listing_page_limit', 20))
    if not 1 <= cap <= 20:
        raise ValueError('Listing page limit must be between 1 and 20')
    queue, seen, documents = [root], set(), []
    while queue:
        url = queue.pop(0)
        if url in seen:
            continue
        if len(seen) >= cap:
            raise ValueError('Pagination exceeds source budget; no partial collection')
        allowed, reason = robots(url)
        if not allowed:
            raise ValueError('Pagination access unavailable: ' + reason)
        if seen:
            pause()
        html = fetch(url)
        seen.add(url)
        documents.append((url, html))
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            next_url = urldefrag(urljoin(url, link['href']))[0]
            parsed = urlparse(next_url)
            if (parsed.scheme == origin.scheme and parsed.hostname == origin.hostname
                    and not parsed.username and not parsed.password and not parsed.port
                    and not parsed.query and re.fullmatch(r'/events/page/[1-9][0-9]*/?', parsed.path)
                    and next_url not in seen and next_url not in queue):
                queue.append(next_url)
    return documents

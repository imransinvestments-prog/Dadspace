"""Conservative, source-local grounding for model family claims.

This is evidence validation, not a model of every activity a family might enjoy.
Unproven listings go to review rather than gaining eligibility from a score.
"""
import re
import unicodedata
from bs4 import BeautifulSoup

FAMILY = re.compile(r"\b(?:famil(?:y|ies)|children|child|kids|kid|bab(?:y|ies)|toddlers?|preschool|pre school|junior|under [0-9]+s?)\b", re.I)


def normalized(value):
    value = unicodedata.normalize('NFKC', str(value or '')).casefold()
    return re.sub(r'[^\w]+', ' ', value).strip()


def grounded(item, documents, prepared):
    """Require a quoted family phrase in the supplied, matching listing context."""
    title = normalized(item.get('title'))
    quote = normalized(item.get('family_evidence'))
    if not title or not quote or not FAMILY.search(quote):
        return False
    if quote not in normalized(prepared):
        return False
    for _, html in documents:
        soup = BeautifulSoup(html, 'html.parser')
        for node in soup.select('nav, header, footer, script, style, form, [role="navigation"]'):
            node.decompose()
        for node in soup.find_all(['h1', 'h2', 'h3', 'h4', 'a', 'strong', 'td']):
            label = normalized(node.get_text(' ', strip=True))
            # A small source subtitle/icon is permitted, invented titles are not.
            if title not in label or len(label) > len(title) + 50:
                continue
            for parent in [node, *list(node.parents)[:6]]:
                if parent.name in ('body', 'html', '[document]'):
                    break
                if node.name in ('a', 'strong', 'td') and parent.name in ('main', 'section', 'ul', 'ol'):
                    break
                # With link-only cards, do not borrow a phrase across sibling
                # listing links merely because their container has no headings.
                other_links = [a for a in parent.find_all('a')
                               if normalized(a.get_text(' ', strip=True))
                               and title not in normalized(a.get_text(' ', strip=True))
                               and not re.fullmatch(r'(?:book|book now|tickets|read more|find out more|more details)',
                                                   normalized(a.get_text(' ', strip=True)))]
                if other_links and node.name == 'a':
                    break
                context = normalized(parent.get_text(' ', strip=True))
                if len(context) > 12000:
                    break
                headings = {normalized(h.get_text(' ', strip=True))
                            for h in parent.find_all(['h1', 'h2', 'h3', 'h4'])}
                # A neighbouring listing or global banner cannot supply evidence.
                if any(title not in heading for heading in headings):
                    break
                if quote in context:
                    return True
    return False


def filter_grounded(raw, documents, prepared, stats):
    if not isinstance(raw, list) or not all(isinstance(x, dict) for x in raw):
        raise ValueError('Invalid listing extraction')
    accepted = []
    for item in raw:
        if grounded(item, documents, prepared):
            accepted.append(item)
        else:
            stats['ungrounded_family_evidence'] = stats.get('ungrounded_family_evidence', 0) + 1
    return accepted

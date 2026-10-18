"""Approved opt-in MyLibrary session contract. No title/location-derived IDs."""
import hashlib
import re
from urllib.parse import urlparse, parse_qs

ADAPTER = 'library_portal_sessions_v1'
SCOPES = {'libraries.ealing.gov.uk': ('ealing.events.mylibrary.digital', {264038, 319285})}


def scope(url):
    host = urlparse(url).hostname
    if host not in SCOPES:
        raise ValueError('Provider identity scope has not been qualified')
    return SCOPES[host]


def metadata(namespace, session_id, occurrences):
    if namespace != SCOPES['libraries.ealing.gov.uk'][0] or not re.fullmatch(r'[1-9][0-9]*', str(session_id)):
        raise ValueError('Invalid provider session identity')
    if int(session_id) not in SCOPES['libraries.ealing.gov.uk'][1]:
        raise ValueError('Session is outside the reviewed scope')
    if not isinstance(occurrences, list) or not 1 <= len(occurrences) <= 200:
        raise ValueError('Explicit occurrence provenance required')
    seen = set()
    for item in occurrences:
        eid = item.get('id')
        link = urlparse(item.get('url', ''))
        if (type(eid) is not int or eid <= 0 or eid in seen or link.scheme != 'https'
                or link.hostname != namespace or link.path != '/event' or link.username or link.password
                or link.port not in (None, 443) or parse_qs(link.query) != {'id': [str(eid)]}
                or link.fragment):
            raise ValueError('Contradictory or duplicate occurrence provenance')
        seen.add(eid)
    return {'provider_namespace': namespace, 'provider_session_id': str(session_id),
            'provider_occurrences': sorted(occurrences, key=lambda r: r['id'])}


def row_identity(item, source, method):
    if source.get('source_adapter') != ADAPTER or method != ADAPTER:
        if any(item.get(key) is not None for key in ('provider_namespace', 'provider_session_id', 'provider_occurrences')):
            raise ValueError('Provider metadata requires the reviewed adapter')
        return None
    namespace, _ = scope(source['url'])
    if item.get('provider_namespace') != namespace:
        raise ValueError('Provider namespace does not match source')
    facts = metadata(namespace, item.get('provider_session_id'), item.get('provider_occurrences'))
    key = hashlib.sha1(f"activity-session-v1|{namespace}|{facts['provider_session_id']}".encode()).hexdigest()
    return key, facts

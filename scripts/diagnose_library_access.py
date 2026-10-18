"""Bounded access evidence for approved portals; no collection or access fallback."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from urllib.robotparser import RobotFileParser

import requests

PORTALS = ('https://libraries.ealing.gov.uk', 'https://libraries.merton.gov.uk')
USER_AGENT = 'Mozilla/5.0 (compatible; DadspaceEventsBot/1.0)'
SAFE_HEADERS = ('server', 'content-type', 'cf-ray', 'cf-mitigated', 'x-vercel-id',
                'x-vercel-error', 'x-cache', 'retry-after')


def inspect_response(response):
    """Retain diagnostic facts, never cookies, credentials or page content."""
    body = response.content[:65536]
    text = body.decode('utf-8', errors='replace')
    title = re.search(r'<title[^>]*>(.*?)</title>', text, re.I | re.S)
    return dict(status=response.status_code,
                headers={key: response.headers[key][:300] for key in SAFE_HEADERS
                         if key in response.headers},
                title=re.sub(r'\s+', ' ', title[1]).strip()[:160] if title else None,
                body_prefix_sha256=hashlib.sha256(body).hexdigest(),
                indicators=[name for name, pattern in (
                    ('cloudflare_challenge', r'cf-chl-|challenge-platform|Just a moment'),
                    ('vercel_checkpoint', r'Vercel Security Checkpoint'),
                    ('access_denied', r'Access Denied|Forbidden'),
                ) if re.search(pattern, text, re.I)])


def diagnose(get=requests.get):
    results = []
    for origin in PORTALS:
        result = dict(origin=origin)
        results.append(result)
        try:
            robots = get(origin+'/robots.txt', headers={'User-Agent': USER_AGENT},
                         timeout=(5, 20), allow_redirects=False)
            result['robots'] = inspect_response(robots)
            if robots.status_code != 200:
                result['events'] = dict(skipped='Robots unavailable; no additional page request')
                continue
            parser = RobotFileParser()
            parser.parse(robots.text.splitlines())
            if not parser.can_fetch(USER_AGENT, origin+'/events'):
                result['events'] = dict(skipped='Robots disallows this page')
                continue
            response = get(origin+'/events', headers={'User-Agent': USER_AGENT},
                           timeout=(5, 20), allow_redirects=False)
            result['events'] = inspect_response(response)
        except requests.RequestException as error:
            # Exception text can contain proxy credentials or incidental URLs.
            result['error_type'] = type(error).__name__
    return dict(checked_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                database_writes=0, model_calls=0, redirects_followed=False, results=results)


if __name__ == '__main__':
    report = diagnose()
    path = Path('mylibrary-source-review/access-diagnostics.json')
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

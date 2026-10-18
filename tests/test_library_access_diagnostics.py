import importlib.util
from pathlib import Path
import unittest

import requests

spec = importlib.util.spec_from_file_location('access', Path(__file__).parents[1]/'scripts/diagnose_library_access.py')
access = importlib.util.module_from_spec(spec)
spec.loader.exec_module(access)


def response(status, text, headers=None):
    result = requests.Response()
    result.status_code = status
    result._content = text.encode()
    result.headers.update(headers or {})
    return result


class AccessDiagnosticsTests(unittest.TestCase):
    def test_robots_denial_and_error_do_not_request_events(self):
        calls = []
        def get(url, **kwargs):
            calls.append(url)
            self.assertFalse(kwargs['allow_redirects'])
            return response(200, 'User-agent: *\nDisallow: /') if len(calls)==1 else response(403, 'Forbidden')
        report = access.diagnose(get)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all('skipped' in item['events'] for item in report['results']))

    def test_denial_facts_exclude_cookies_and_do_not_trigger_fallback(self):
        calls = []
        def get(url, **kwargs):
            calls.append(url)
            if url.endswith('/robots.txt'):
                return response(200, 'User-agent: *\nAllow: /')
            return response(403, '<title>Just a moment...</title>challenge-platform private-body',
                            {'server':'cloudflare', 'cf-ray':'trace-id', 'set-cookie':'secret'})
        report = access.diagnose(get)
        self.assertEqual(len(calls), 4)
        for item in report['results']:
            self.assertEqual(item['events']['status'], 403)
            self.assertIn('cloudflare_challenge', item['events']['indicators'])
            self.assertNotIn('set-cookie', item['events']['headers'])
        self.assertNotIn('private-body', str(report))
        self.assertNotIn('secret', str(report))


if __name__ == '__main__':
    unittest.main()

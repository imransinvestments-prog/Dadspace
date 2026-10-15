import json
from io import BytesIO
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from scripts.diagnose_gemini_access import safe_error, rest_probe, redacted_message


class AccessTests(unittest.TestCase):
    def test_flat_sdk_errors_and_reason_signals_are_sanitized(self):
        result = safe_error({'status': 'PERMISSION_DENIED',
                            'message': 'Permission denied on resource project private-id'})
        self.assertEqual(result['status'], 'PERMISSION_DENIED')
        self.assertEqual(result['denial_signals'], ['resource_permission'])
        self.assertNotIn('private-id', json.dumps(result))

    def test_sanitizes_error_details_and_leak_classification(self):
        result = safe_error({'error': {'status': 'PERMISSION_DENIED',
            'message': 'secret-key was reported as leaked; project private',
            'details': [{'reason': 'API_KEY_SERVICE_BLOCKED', 'metadata': {'consumer': 'private'}},
                        {'reason': 'private-unknown'}]}}, 'secret-key')
        self.assertTrue(result['known_leaked_key_message'])
        self.assertEqual(result['reasons'], ['API_KEY_SERVICE_BLOCKED'])
        self.assertNotIn('private', json.dumps(result))
        self.assertNotIn('secret-key', json.dumps(result))

    def test_message_preserves_cause_without_credentials_or_identifiers(self):
        result = redacted_message('Caller lacks permission: unusual-secret https://host/key?q=x '
                                  'user@example.com projects/private-id 511384296448\n\x1b[31m',
                                  'unusual-secret')
        self.assertIn('Caller lacks permission', result)
        for value in ('unusual-secret', 'https://host', 'user@example.com',
                      'private-id', '511384296448', '\n', '\x1b'):
            self.assertNotIn(value, result)
        self.assertEqual(len(redacted_message('x' * 2000)), 1200)

    @patch('scripts.diagnose_gemini_access.urlopen')
    def test_rest_error_includes_redacted_explanation(self, opener):
        body = json.dumps({'error': {'status': 'PERMISSION_DENIED',
            'message': 'Service account for actual-secret lacks permission'}}).encode()
        opener.side_effect = HTTPError('url', 403, 'denied', {}, BytesIO(body))
        result = rest_probe('actual-secret', 'gemini-test')
        self.assertIn('lacks permission', result['message_redacted'])
        self.assertNotIn('actual-secret', json.dumps(result))

    @patch('scripts.diagnose_gemini_access.urlopen')
    def test_only_one_metadata_get_no_generation_or_key_in_url(self, opener):
        opener.side_effect = HTTPError('private', 403, 'private', {}, BytesIO(b'<html>private</html>'))
        self.assertEqual(rest_probe('secret', 'gemini-test'), {'http_status': 403, 'body_kind': 'non-json'})
        opener.assert_called_once()
        request = opener.call_args.args[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertNotIn('secret', request.full_url)
        self.assertNotIn('generateContent', request.full_url)

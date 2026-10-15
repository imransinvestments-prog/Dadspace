import json
from io import BytesIO
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from scripts.diagnose_gemini_access import safe_error, rest_probe


class AccessTests(unittest.TestCase):
    def test_sanitizes_error_details_and_leak_classification(self):
        result = safe_error({'error': {'status': 'PERMISSION_DENIED',
            'message': 'secret-key was reported as leaked; project private',
            'details': [{'reason': 'API_KEY_SERVICE_BLOCKED', 'metadata': {'consumer': 'private'}},
                        {'reason': 'private-unknown'}]}})
        self.assertTrue(result['known_leaked_key_message'])
        self.assertEqual(result['reasons'], ['API_KEY_SERVICE_BLOCKED'])
        self.assertNotIn('private', json.dumps(result))
        self.assertNotIn('secret-key', json.dumps(result))

    @patch('scripts.diagnose_gemini_access.urlopen')
    def test_only_one_metadata_get_no_generation_or_key_in_url(self, opener):
        opener.side_effect = HTTPError('private', 403, 'private', {}, BytesIO(b'<html>private</html>'))
        self.assertEqual(rest_probe('secret', 'gemini-test'), {'http_status': 403, 'body_kind': 'non-json'})
        opener.assert_called_once()
        request = opener.call_args.args[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertNotIn('secret', request.full_url)
        self.assertNotIn('generateContent', request.full_url)

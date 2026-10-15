"""Non-generating probes with bounded, redacted Google error explanations."""
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REASONS = {'API_KEY_INVALID', 'API_KEY_EXPIRED', 'API_KEY_NOT_FOUND',
           'API_KEY_SERVICE_BLOCKED', 'API_KEY_HTTP_REFERRER_BLOCKED',
           'API_KEY_IP_ADDRESS_BLOCKED', 'SERVICE_DISABLED', 'BILLING_DISABLED',
           'CONSUMER_INVALID', 'CONSUMER_SUSPENDED', 'SECURITY_POLICY_VIOLATED'}
STATUSES = {'PERMISSION_DENIED', 'UNAUTHENTICATED', 'NOT_FOUND', 'INVALID_ARGUMENT',
            'RESOURCE_EXHAUSTED', 'FAILED_PRECONDITION', 'UNAVAILABLE', 'INTERNAL'}
SIGNALS = {
    'invalid_key': ('api key not valid', 'api key is invalid'),
    'expired_key': ('api key expired', 'api key is expired'),
    'suspended_key': ('api key has been suspended', 'api key is suspended'),
    'blocked_key': ('api key has been blocked', 'api key is blocked'),
    'caller_permission': ('caller does not have permission',),
    'unregistered_caller': ("method doesn't allow unregistered callers",),
    'unsupported_key_auth': ('api keys are not supported',),
    'service_restriction': ('requests to this api',),
    'service_not_enabled': ('has not been used in project', 'api is disabled'),
    'ip_restriction': ('requests from ip address',),
    'referrer_restriction': ('requests from referer', 'requests from referrer'),
    'insufficient_scopes': ('insufficient authentication scopes',),
    'location_restriction': ('location is not supported',),
    'organization_policy': ("organization's policy", 'organization policy'),
    'billing_disabled': ('billing account is disabled', 'billing is disabled'),
    'resource_permission': ('permission denied on resource',),
}


def redacted_message(message, key=''):
    text = str(message)
    # Remove the exact credential first, including nonstandard key formats.
    if key:
        text = text.replace(key, '[REDACTED_KEY]')
    text = re.sub(r'https?://\S+', '[REDACTED_URL]', text)
    text = re.sub(r'[\w.+-]+@[\w.-]+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'\b(?:AIza|AQ\.)[A-Za-z0-9_.-]+', '[REDACTED_KEY]', text)
    text = re.sub(r'\b(?:projects|consumers)/[A-Za-z0-9_.:-]+', '[REDACTED_RESOURCE]', text)
    text = re.sub(r'(?i)\b(project(?: id)?\s+)[A-Za-z0-9_-]+', r'\1[REDACTED_PROJECT]', text)
    text = re.sub(r'\b\d{6,}\b', '[REDACTED_ID]', text)
    # No terminal control sequences or multiline log injection.
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
    return text[:1200]


def safe_error(payload, key=''):
    error = payload.get('error', payload) if isinstance(payload, dict) else {}
    status = error.get('status')
    reasons = [detail['reason'] for detail in error.get('details', [])
               if isinstance(detail, dict) and detail.get('reason') in REASONS]
    # Classify documented messages locally without exposing any remote text.
    message = str(error.get('message', '')).lower()
    return {'status': status if status in STATUSES else 'unknown',
            'message_redacted': redacted_message(error.get('message', ''), key),
            'reasons': sorted(set(reasons)),
            'denial_signals': [name for name, phrases in SIGNALS.items()
                               if any(phrase in message for phrase in phrases)],
            'known_leaked_key_message': 'reported as leaked' in message or 'key was leaked' in message,
            'project_denied_message': 'project has been denied access' in message}


def rest_probe(key, model, catalogue=False):
    path = 'models?pageSize=1000' if catalogue else 'models/' + model
    req = Request('https://generativelanguage.googleapis.com/v1beta/' + path,
                  headers={'x-goog-api-key': key}, method='GET')
    try:
        with urlopen(req, timeout=30) as response:
            payload = json.load(response)
            if catalogue:
                return {'http_status': response.status,
                        'configured_model_listed': any(item.get('name') == 'models/' + model
                                                      for item in payload.get('models', [])),
                        'more_pages': bool(payload.get('nextPageToken'))}
            return {'http_status': response.status,
                    'supports_generate_content': 'generateContent' in payload.get('supportedGenerationMethods', [])}
    except HTTPError as exc:
        raw = exc.read(65536)
        try:
            detail = safe_error(json.loads(raw), key)
            body_kind = 'json'
        except (ValueError, UnicodeError):
            detail, body_kind = {}, 'non-json'
        return {'http_status': exc.code, 'body_kind': body_kind, **detail}
    except Exception as exc:
        return {'error_type': type(exc).__name__}


def sdk_probe(key, model):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=key, http_options=types.HttpOptions(
        timeout=30000, retry_options=types.HttpRetryOptions(attempts=1)))
    try:
        info = client.models.get(model=model)
        return {'http_status': 200, 'supports_generate_content': 'generateContent' in (info.supported_actions or [])}
    except Exception as exc:
        code = getattr(exc, 'code', None)
        payload = getattr(exc, 'response_json', {})
        if not payload and isinstance(getattr(exc, 'details', None), dict):
            payload = exc.details
        detail = safe_error(payload, key)
        return {'http_status': code if isinstance(code, int) else None,
                'error_type': type(exc).__name__, **detail}
    finally:
        client.close()


def main():
    key = os.environ.get('GEMINI_API_KEY', '')
    model = os.environ.get('DIAGNOSTIC_MODEL', 'gemini-3.6-flash')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', model):
        raise ValueError('Invalid diagnostic model')
    report = {'model': model, 'generation_requests': 0, 'database_access': False,
              'credential_present': bool(key), 'credential_outer_whitespace': key != key.strip(),
              'credential_wrapped_quotes': bool(key) and key[0] in ('"', "'"),
              'note': 'Metadata access alone does not prove generateContent permission'}
    if key:
        report.update(rest=rest_probe(key, model), sdk=sdk_probe(key, model),
                      catalogue=rest_probe(key, model, catalogue=True))
    Path('gemini-access-diagnostic.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

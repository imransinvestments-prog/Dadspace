"""Non-generating Gemini model metadata probes; never logs remote error text."""
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


def safe_error(payload):
    error = payload.get('error', {}) if isinstance(payload, dict) else {}
    status = error.get('status')
    reasons = [detail['reason'] for detail in error.get('details', [])
               if isinstance(detail, dict) and detail.get('reason') in REASONS]
    # Classify documented messages locally without exposing any remote text.
    message = str(error.get('message', '')).lower()
    return {'status': status if status in STATUSES else 'unknown',
            'reasons': sorted(set(reasons)),
            'known_leaked_key_message': 'reported as leaked' in message or 'key was leaked' in message,
            'project_denied_message': 'project has been denied access' in message}


def rest_probe(key, model):
    req = Request('https://generativelanguage.googleapis.com/v1beta/models/' + model,
                  headers={'x-goog-api-key': key}, method='GET')
    try:
        with urlopen(req, timeout=30) as response:
            payload = json.load(response)
            return {'http_status': response.status,
                    'supports_generate_content': 'generateContent' in payload.get('supportedGenerationMethods', [])}
    except HTTPError as exc:
        raw = exc.read(65536)
        try:
            detail = safe_error(json.loads(raw))
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
        detail = safe_error(getattr(exc, 'response_json', {}))
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
              'note': 'Metadata access alone does not prove generateContent permission'}
    if key:
        report.update(rest=rest_probe(key, model), sdk=sdk_probe(key, model))
    Path('gemini-access-diagnostic.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

"""Server-side structured generation. Explicit selection; never automatic fallback."""
import copy
import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from gemini_usage import BudgetExhausted


class FatalLLMError(RuntimeError):
    """Credentials, billing or configuration require operator intervention."""


KEYS = {'gemini': 'GEMINI_API_KEY', 'openai': 'OPENAI_API_KEY', 'deepseek': 'DEEPSEEK_API_KEY'}


def selection(scope='EXTRACTION', legacy_model='gemini-3.6-flash'):
    provider = (os.getenv(scope + '_LLM_PROVIDER') or os.getenv('LLM_PROVIDER') or 'gemini').strip().lower()
    if provider not in KEYS:
        raise FatalLLMError('LLM_PROVIDER must be gemini, openai or deepseek')
    model = os.getenv(scope + '_LLM_MODEL') or os.getenv('LLM_MODEL')
    if not model and provider == 'gemini':
        model = legacy_model
    if not model or not re.fullmatch(r'[a-zA-Z0-9_.:-]+', model):
        raise FatalLLMError('Set an explicit valid LLM_MODEL for the selected provider')
    return provider, model


def credential_name(scope='EXTRACTION'):
    # Credential checks do not need a model or inspect/print the secret value.
    provider = (os.getenv(scope + '_LLM_PROVIDER') or os.getenv('LLM_PROVIDER') or 'gemini').strip().lower()
    if provider not in KEYS:
        raise FatalLLMError('Unsupported LLM_PROVIDER')
    return KEYS[provider]


def strict_schema(schema):
    """OpenAI requires an object root and every property explicitly required."""
    result = copy.deepcopy(schema)
    def walk(node):
        if isinstance(node, dict):
            node.pop('default', None)
            if node.get('type') == 'object':
                node['additionalProperties'] = False
                node['required'] = list(node.get('properties', {}))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(result)
    if result.get('type') == 'array':
        # Keep definitions at the document root so #/$defs references still work.
        definitions = result.pop('$defs', None)
        result = {'type': 'object', 'properties': {'items': result},
                  'required': ['items'], 'additionalProperties': False}
        if definitions:
            result['$defs'] = definitions
        return result, True
    if result.get('type') != 'object':
        raise FatalLLMError('Structured output requires an object or array schema')
    return result, False


def _post(url, key, body, timeout, gemini=False):
    headers = {'Content-Type': 'application/json'}
    headers['x-goog-api-key' if gemini else 'Authorization'] = key if gemini else 'Bearer ' + key
    with urlopen(Request(url, headers=headers, data=json.dumps(body).encode('utf-8')), timeout=timeout) as response:
        return json.load(response)


class StructuredGenerator:
    def __init__(self, scope, legacy_model, timeout=90, output_limit=6000, thinking_level='', temperature=None):
        self.provider, self.model = selection(scope, legacy_model)
        self.key = os.getenv(KEYS[self.provider])
        if not self.key:
            raise FatalLLMError(KEYS[self.provider] + ' is missing')
        self.timeout = timeout
        self.thinking_level = os.getenv('GEMINI_THINKING_LEVEL', '').strip().lower() or thinking_level
        self.temperature = temperature
        def integer(name, default):
            value = int(os.getenv('LLM_' + name) or os.getenv('GEMINI_' + name) or default)
            if value < 0:
                raise FatalLLMError(name + ' must be non-negative')
            return value
        self.retries = integer('MAX_RETRIES', 2)
        if self.retries > 5:
            raise FatalLLMError('LLM_MAX_RETRIES must be at most 5')
        self.token_budget = integer('RUN_TOKEN_BUDGET', 0)
        self.attempt_budget = integer('RUN_MAX_ATTEMPTS', 0)
        self.output_limit = integer('MAX_OUTPUT_TOKENS', output_limit)
        self.metrics = dict(api_attempts=0, input_chars_sent=0, prompt_tokens=0,
                            output_tokens=0, thinking_tokens=0, total_tokens=0,
                            unknown_usage_attempts=0, unknown_thinking_attempts=0)
        self.settings = dict(provider=self.provider, model=self.model,
                             thinking_level='provider-default', token_budget=self.token_budget,
                             attempt_budget=self.attempt_budget, max_output_tokens=self.output_limit,
                             max_retries=self.retries)

    def close(self):
        pass  # HTTP responses are closed within each request.

    def generate(self, prompt, schema):
        from jsonschema import Draft202012Validator
        normalized, wrapped = strict_schema(schema)
        Draft202012Validator.check_schema(normalized)
        sent_prompt = prompt
        if self.provider == 'openai':
            url = 'https://api.openai.com/v1/responses'
            body = {'model': self.model, 'input': prompt, 'store': False,
                    'text': {'format': {'type': 'json_schema', 'name': 'dadspace',
                                        'schema': normalized, 'strict': True}}}
            limit_name = 'max_output_tokens'
        elif self.provider == 'deepseek':
            url = 'https://api.deepseek.com/chat/completions'
            sent_prompt += '\nReturn JSON matching this schema: ' + json.dumps(normalized)
            body = {'model': self.model, 'messages': [{'role': 'user', 'content': sent_prompt}],
                    'response_format': {'type': 'json_object'}}
            limit_name = 'max_tokens'
        else:
            url = 'https://generativelanguage.googleapis.com/v1beta/models/' + self.model + ':generateContent'
            # REST Gemini uses its own schema dialect. responseJsonSchema accepts JSON Schema.
            body = {'contents': [{'parts': [{'text': prompt}]}], 'generationConfig': {
                'responseMimeType': 'application/json', 'responseJsonSchema': normalized}}
            if self.temperature is not None:
                body['generationConfig']['temperature'] = self.temperature
            level = self.thinking_level
            if level:
                if level not in {'minimal', 'low', 'medium', 'high'}:
                    raise FatalLLMError('Invalid GEMINI_THINKING_LEVEL')
                body['generationConfig']['thinkingConfig'] = {'thinkingLevel': level.upper()}
            limit_name = 'maxOutputTokens'
        if self.output_limit:
            (body['generationConfig'] if self.provider == 'gemini' else body)[limit_name] = self.output_limit
        for attempt in range(self.retries + 1):
            if self.attempt_budget and self.metrics['api_attempts'] >= self.attempt_budget:
                raise BudgetExhausted('LLM request budget exhausted')
            if self.token_budget and (self.metrics['total_tokens'] >= self.token_budget or self.metrics['unknown_usage_attempts']):
                raise BudgetExhausted('LLM token budget exhausted or usage unavailable')
            self.metrics['api_attempts'] += 1
            self.metrics['input_chars_sent'] += len(sent_prompt)
            try:
                reply = _post(url, self.key, body, self.timeout, self.provider == 'gemini')
            except ValueError:
                self.metrics['unknown_usage_attempts'] += 1
                raise RuntimeError(self.provider + ' returned an invalid HTTP JSON response') from None
            except (HTTPError, URLError, TimeoutError) as exc:
                self.metrics['unknown_usage_attempts'] += 1
                code = getattr(exc, 'code', None)
                if code in {400, 401, 402, 403, 404, 422}:
                    raise FatalLLMError(f'{self.provider} rejected request (HTTP {code}); check billing, model and credentials') from None
                if code is not None and code != 429 and not 500 <= code <= 599:
                    raise RuntimeError(f'{self.provider} HTTP {code}') from None
                if attempt == self.retries:
                    raise RuntimeError(self.provider + ' transport failed after bounded retries') from None
                time.sleep(min(2 ** attempt, 8))
                continue
            self._usage(reply)
            if self.provider == 'openai':
                if reply.get('status') != 'completed':
                    raise ValueError('OpenAI incomplete output rejected')
                parts = [p for item in reply.get('output', []) for p in item.get('content', [])]
                if any(p.get('type') == 'refusal' for p in parts):
                    raise ValueError('OpenAI refusal rejected')
                text = ''.join(p.get('text', '') for p in parts if p.get('type') == 'output_text')
            elif self.provider == 'deepseek':
                choices = reply.get('choices') or []
                if len(choices) != 1 or choices[0].get('finish_reason') != 'stop':
                    raise ValueError('DeepSeek incomplete output rejected')
                text = choices[0]['message'].get('content', '')
            else:
                candidates = reply.get('candidates') or []
                if not candidates or candidates[0].get('finishReason') != 'STOP':
                    raise ValueError('Gemini incomplete output rejected')
                text = ''.join(p.get('text', '') for p in candidates[0].get('content', {}).get('parts', []) if not p.get('thought'))
            data = json.loads(text)
            # No retry/fallback on malformed content, refusal or failed validation.
            if not Draft202012Validator(normalized).is_valid(data):
                raise ValueError(self.provider + ' returned data outside the requested schema')
            return data['items'] if wrapped else data

    def _usage(self, reply):
        usage = reply.get('usageMetadata' if self.provider == 'gemini' else 'usage') or {}
        if self.provider == 'gemini':
            incoming, outgoing, total = 'promptTokenCount', 'candidatesTokenCount', 'totalTokenCount'
            thinking = usage.get('thoughtsTokenCount')
        elif self.provider == 'openai':
            incoming, outgoing, total = 'input_tokens', 'output_tokens', 'total_tokens'
            thinking = (usage.get('output_tokens_details') or {}).get('reasoning_tokens')
        else:
            incoming, outgoing, total = 'prompt_tokens', 'completion_tokens', 'total_tokens'
            thinking = (usage.get('completion_tokens_details') or {}).get('reasoning_tokens')
        if any(usage.get(k) is None for k in (incoming, outgoing, total)):
            self.metrics['unknown_usage_attempts'] += 1
        if thinking is None:
            self.metrics['unknown_thinking_attempts'] += 1
        self.metrics['prompt_tokens'] += int(usage.get(incoming) or 0)
        self.metrics['output_tokens'] += int(usage.get(outgoing) or 0) + (int(thinking or 0) if self.provider == 'gemini' else 0)
        self.metrics['thinking_tokens'] += int(thinking or 0)
        self.metrics['total_tokens'] += int(usage.get(total) or 0)


def make_extractor(model, schema, timeout, fatal_error):
    provider, selected_model = selection('EXTRACTION', model)
    if provider == 'gemini':
        # Preserve the tested Gemini SDK extraction behavior and legacy controls.
        from gemini_usage import make_extractor as legacy
        call = legacy(selected_model, schema, timeout, fatal_error)
        call.settings['provider'] = 'gemini'
        return call
    from pydantic import TypeAdapter
    generator = StructuredGenerator('EXTRACTION', model, timeout)
    json_schema = TypeAdapter(schema).json_schema()
    def call(prompt):
        try:
            return generator.generate(prompt, json_schema)
        except FatalLLMError as exc:
            raise fatal_error(str(exc)) from None
    call.metrics, call.settings, call.close = generator.metrics, generator.settings, generator.close
    return call

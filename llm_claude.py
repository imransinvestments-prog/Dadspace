"""Claude structured generation through the official Anthropic SDK.

One request per call. llm_provider owns retries, budgets and schema validation, so
the SDK's own retries are off. No remote message text is copied into errors.
"""
import copy

from llm_provider import FatalLLMError, TransientLLMError

# Claude's structured outputs reject these keywords. They are dropped from the schema
# sent to the API only; llm_provider still validates the reply against the full schema.
UNSUPPORTED = {'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf',
               'minLength', 'maxLength', 'pattern', 'minItems', 'maxItems', 'uniqueItems'}
STOP_REASONS = {'end_turn', 'max_tokens', 'refusal', 'stop_sequence', 'pause_turn', 'tool_use'}


def api_schema(schema):
    """Strip unsupported keywords from schema nodes, never from property names."""
    result = copy.deepcopy(schema)
    def walk(node):
        if not isinstance(node, dict):
            return
        for keyword in UNSUPPORTED & set(node):
            del node[keyword]
        for child in (node.get('properties') or {}).values():
            walk(child)
        for child in (node.get('$defs') or {}).values():
            walk(child)
        for key in ('anyOf', 'allOf', 'oneOf'):
            for child in node.get(key) or []:
                walk(child)
        if isinstance(node.get('items'), dict):
            walk(node['items'])
    walk(result)
    return result


def request(model, key, prompt, schema, output_limit, timeout, effort):
    import anthropic
    client = anthropic.Anthropic(api_key=key, timeout=timeout, max_retries=0)
    try:
        message = client.messages.create(
            model=model,
            max_tokens=output_limit or 16000,
            messages=[{'role': 'user', 'content': prompt}],
            output_config={'effort': effort,
                           'format': {'type': 'json_schema', 'schema': api_schema(schema)}})
    except anthropic.APIStatusError as exc:
        # 429 and overload/5xx are retryable; anything else (bad key, low credit, bad model) needs an operator.
        if exc.status_code == 429 or exc.status_code >= 500:
            raise TransientLLMError(f'HTTP {exc.status_code}') from None
        raise FatalLLMError(f'anthropic rejected request (HTTP {exc.status_code}); check billing, model and credentials') from None
    except anthropic.APIConnectionError as exc:  # includes APITimeoutError
        raise TransientLLMError(type(exc).__name__) from None
    usage = message.usage
    cached = (getattr(usage, 'cache_creation_input_tokens', None) or 0) + (getattr(usage, 'cache_read_input_tokens', None) or 0)
    incoming = None if usage.input_tokens is None else usage.input_tokens + cached
    total = None if incoming is None or usage.output_tokens is None else incoming + usage.output_tokens
    stop = message.stop_reason if message.stop_reason in STOP_REASONS else 'unknown'
    text = ''.join(block.text for block in message.content if block.type == 'text')
    return {'stop_reason': stop, 'text': text,
            'usage': {'input_tokens': incoming, 'output_tokens': usage.output_tokens, 'total_tokens': total}}

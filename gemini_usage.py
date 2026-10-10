"""Gemini extraction controls; provider selection belongs to issue #66."""
import json
import os
import time


class BudgetExhausted(RuntimeError):
    """Stop before another request, without marking a source checked."""


def make_extractor(model, schema, timeout, fatal_error):
    from google import genai
    from google.genai import types

    def integer(name, default=0):
        value = int(os.environ.get(name) or default)
        if value < 0:
            raise ValueError(f"{name} must be non-negative")
        return value

    level = os.environ.get("GEMINI_THINKING_LEVEL", "").strip().lower()
    if level and level not in {"minimal", "low", "medium", "high"}:
        raise ValueError("Invalid GEMINI_THINKING_LEVEL")
    token_budget = integer("GEMINI_RUN_TOKEN_BUDGET")
    attempt_budget = integer("GEMINI_RUN_MAX_ATTEMPTS")
    output_limit = integer("GEMINI_MAX_OUTPUT_TOKENS")
    retries = integer("GEMINI_MAX_RETRIES", 2)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise fatal_error("GEMINI_API_KEY is missing")
    # Let this module own retries. HTTP timeout bounds the actual network call.
    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(
        timeout=timeout * 1000, retry_options=types.HttpRetryOptions(attempts=1)))
    metrics = dict(api_attempts=0, input_chars_sent=0, prompt_tokens=0,
                   output_tokens=0, thinking_tokens=0, total_tokens=0,
                   unknown_usage_attempts=0)
    config = dict(response_mime_type="application/json", response_schema=schema,
                  temperature=0,
                  automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
    if level:
        config["thinking_config"] = types.ThinkingConfig(thinking_level=level)
    if output_limit:
        config["max_output_tokens"] = output_limit

    def call(prompt):
        last_error = None
        for attempt in range(retries + 1):
            if attempt_budget and metrics["api_attempts"] >= attempt_budget:
                raise BudgetExhausted("Gemini request budget exhausted")
            if token_budget and (metrics["total_tokens"] >= token_budget or metrics["unknown_usage_attempts"]):
                raise BudgetExhausted("Gemini token budget exhausted or usage unavailable")
            metrics["api_attempts"] += 1
            metrics["input_chars_sent"] += len(prompt)
            response = None
            try:
                response = client.models.generate_content(
                    model=model, contents=prompt, config=types.GenerateContentConfig(**config))
                usage = getattr(response, "usage_metadata", None)
                if usage is None:
                    metrics["unknown_usage_attempts"] += 1
                else:
                    thinking = int(getattr(usage, "thoughts_token_count", 0) or 0)
                    metrics["prompt_tokens"] += int(getattr(usage, "prompt_token_count", 0) or 0)
                    metrics["thinking_tokens"] += thinking
                    metrics["output_tokens"] += int(getattr(usage, "candidates_token_count", 0) or 0) + thinking
                    total = getattr(usage, "total_token_count", None)
                    if total is None:
                        metrics["unknown_usage_attempts"] += 1
                    else:
                        metrics["total_tokens"] += int(total)
                candidates = getattr(response, "candidates", None) or []
                if not candidates or str(candidates[0].finish_reason).split(".")[-1] != "STOP":
                    raise ValueError("Gemini did not finish cleanly; extraction rejected")
                data = json.loads(response.text)
                if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
                    raise ValueError("Gemini did not return a list of objects")
                return data
            except Exception as exc:
                if response is None:
                    metrics["unknown_usage_attempts"] += 1
                text = str(exc)
                if any(word in text for word in ("NOT_FOUND", "PERMISSION_DENIED", "UNAUTHENTICATED", "INVALID_ARGUMENT", "API key not valid")):
                    raise fatal_error("Gemini rejected the request; check model and credentials") from exc
                last_error = exc
                if attempt < retries:
                    time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"Gemini failed after {retries + 1} attempts: {last_error}")

    call.metrics = metrics
    call.close = client.close
    call.settings = dict(model=model, thinking_level=level or "model-default",
                         token_budget=token_budget, attempt_budget=attempt_budget,
                         max_output_tokens=output_limit, max_retries=retries)
    return call

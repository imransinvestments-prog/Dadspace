"""Best-effort sampling of production Gemini calls; never makes another request."""
import json
import os
from pathlib import Path


def capture_calls(call):
    directory = os.environ.get('SHADOW_CAPTURE_DIR', '')
    if not directory:
        return call
    count = 0

    def wrapped(prompt):
        nonlocal count
        before = dict(call.metrics)
        raw = call(prompt)  # Production errors/return values retain their behavior.
        if count < 2:
            count += 1
            try:
                if not call.json_schema:
                    raise ValueError('No captured response schema')
                snapshot = {'worker': os.environ.get('WORKER_NAME', 'events'),
                    'prompt': prompt, 'schema': call.json_schema, 'raw': raw,
                    'settings': call.settings,
                    'usage': {k: v - before.get(k, 0) for k, v in call.metrics.items()}}
                path = Path(directory)
                path.mkdir(parents=True, exist_ok=True)
                (path / f'sample-{count}.json').write_text(json.dumps(snapshot, ensure_ascii=False), encoding='utf-8')
            except Exception as exc:
                # Artifact capture must never break publication or reveal errors.
                print(f'Shadow capture unavailable: {type(exc).__name__}')
        return raw
    wrapped.metrics, wrapped.settings, wrapped.close = call.metrics, call.settings, call.close
    return wrapped

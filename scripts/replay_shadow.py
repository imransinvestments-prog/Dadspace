"""Replay bounded captured prompts with OpenAI. Has no database or publisher code."""
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from llm_provider import StructuredGenerator, FatalLLMError
from gemini_usage import BudgetExhausted

FIELDS = ('title', 'start_date', 'end_date', 'time_text', 'schedule_text', 'location',
          'venue_name', 'venue_address', 'postcode', 'event_url', 'cost_text', 'age_range',
          'recurrence', 'listing_type', 'family_relevance', 'audience', 'family_evidence')


def estimate(usage, prefix):
    rates = [os.environ.get(prefix + '_' + x + '_USD_PER_MILLION', '') for x in ('INPUT', 'OUTPUT')]
    if not all(rates) or usage.get('unknown_usage_attempts', 0):
        return None
    values = [float(x) for x in rates]
    if not all(math.isfinite(x) and x >= 0 for x in values):
        raise ValueError('Pricing rates must be finite non-negative numbers')
    return (usage['prompt_tokens'] * values[0] + usage['output_tokens'] * values[1]) / 1_000_000


def compare(before, after):
    def keyed(rows):
        return {(str(r.get('event_url') or ''), str(r.get('start_date') or ''), str(r.get('title') or '').lower()): r
                for r in rows}
    left, right = keyed(before), keyed(after)
    return {'baseline_raw_count': len(before), 'shadow_raw_count': len(after),
            'missing': [list(k) for k in left.keys() - right.keys()],
            'added': [list(k) for k in right.keys() - left.keys()],
            'changed': [{'listing': list(k), 'fields': [f for f in FIELDS if left[k].get(f) != right[k].get(f)]}
                        for k in left.keys() & right.keys()
                        if any(left[k].get(f) != right[k].get(f) for f in FIELDS)]}


def replay(directory, output, generator):
    report = {'database_access': False, 'publishing': False, 'samples': [],
              'cost_basis': 'Configured standard rates; uncached-input estimate, not a billing receipt',
              'upstream_run_id': os.environ.get('UPSTREAM_RUN_ID'), 'settings': generator.settings}
    output.mkdir(parents=True, exist_ok=True)
    try:
        for prefix in ('BASELINE', 'SHADOW'):
            estimate({'prompt_tokens': 0, 'output_tokens': 0}, prefix)
        for path in sorted(directory.rglob('sample-*.json'))[:4]:
            if path.stat().st_size > 500_000:
                raise ValueError('Capture outside bounded artifact size')
            snapshot = json.loads(path.read_text(encoding='utf-8'))
            prompt = snapshot['prompt']
            if not isinstance(prompt, str) or len(prompt) > 70000:
                raise ValueError('Captured prompt outside bounded review size')
            if not isinstance(snapshot['raw'], list) or not all(isinstance(x, dict) for x in snapshot['raw']):
                raise ValueError('Invalid baseline result')
            before = dict(generator.metrics)
            raw = generator.generate(prompt, snapshot['schema'])
            usage = {k: v - before.get(k, 0) for k, v in generator.metrics.items()}
            report['samples'].append({'worker': snapshot['worker'],
                'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                'baseline_settings': snapshot['settings'], 'baseline_usage': snapshot['usage'],
                'shadow_usage': usage, 'baseline_estimated_usd': estimate(snapshot['usage'], 'BASELINE'),
                'shadow_estimated_usd': estimate(usage, 'SHADOW'),
                'comparison': compare(snapshot['raw'], raw), 'baseline_raw': snapshot['raw'], 'shadow_raw': raw})
    except Exception as exc:
        report['stopped'] = type(exc).__name__ + '; no retry or fallback'
        raise
    finally:
        report['metrics'] = dict(generator.metrics)
        (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    paths = list(Path('shadow-input').rglob('sample-*.json'))
    if not paths:
        Path('shadow-results').mkdir(exist_ok=True)
        Path('shadow-results/results.json').write_text(json.dumps({'samples': [], 'reason': 'No successful captured Gemini calls; no shadow API calls'}))
    else:
        generator = StructuredGenerator('EXTRACTION', 'gemini-3.6-flash', 90)
        try:
            replay(Path('shadow-input'), Path('shadow-results'), generator)
        finally:
            generator.close()

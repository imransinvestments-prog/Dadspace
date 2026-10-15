"""Replay bounded captured prompts with OpenAI. Has no database or publisher code."""
import hashlib
import json
import math
import os
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from llm_provider import StructuredGenerator, FatalLLMError, IncompleteOutputError
from gemini_usage import BudgetExhausted

FIELDS = ('title', 'start_date', 'end_date', 'time_text', 'schedule_text', 'location',
          'venue_name', 'venue_address', 'postcode', 'event_url', 'cost_text', 'age_range',
          'recurrence', 'listing_type', 'family_relevance', 'audience', 'family_evidence')

# Explicit documented model IDs only; unknown IDs are reported without a request.
LOWEST_THINKING = {
    'gemini-3.6-flash': 'minimal', 'gemini-3.5-flash': 'minimal',
    'gemini-3-flash': 'minimal', 'gemini-3.5-flash-lite': 'minimal',
    'gemini-3.1-flash-lite': 'minimal', 'gemini-3.8-flash': 'low',
    'gemini-3.1-pro': 'low',
}


def configure_minimum(snapshot, generator):
    if generator.provider != 'gemini':
        raise ValueError('Minimum-thinking replay requires Gemini')
    model = snapshot['settings'].get('model')
    level = LOWEST_THINKING.get(model)
    if level is None:
        return False
    generator.model, generator.thinking_level, generator.temperature = model, level, 0
    generator.preserve_gemini_schema = True
    generator.settings.update(model=model, thinking_level=level, temperature=0)
    return True


def estimate(usage, prefix):
    rates = [os.environ.get(prefix + '_' + x + '_USD_PER_MILLION', '') for x in ('INPUT', 'OUTPUT')]
    if not all(rates) or usage.get('unknown_usage_attempts', 0) or any(
            key not in usage for key in ('prompt_tokens', 'output_tokens')):
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


def select_samples(directory):
    """Interleave workers before spending; one worker cannot take every slot."""
    groups = {}
    for path in sorted(directory.rglob('sample-*.json')):
        if path.stat().st_size > 500_000:
            raise ValueError('Capture outside bounded artifact size')
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        groups.setdefault(snapshot['worker'], []).append((path, snapshot))
    selected = []
    while any(groups.values()) and len(selected) < 4:
        for worker in sorted(groups):
            if groups[worker] and len(selected) < 4:
                selected.append(groups[worker].pop(0))
    return selected


def score_reference(reference, rows):
    """Conservative exact evidence scoring; ambiguity never becomes acceptance."""
    if reference.get('kind') != 'human-reviewed-source':
        return None
    scores = []
    used = set()
    for candidate in reference['expected']:
        fields = candidate['fields']
        matches = [(i, row) for i, row in enumerate(rows)
                   if fields.get('event_url') and row.get('event_url') == fields['event_url']
                   and row.get('start_date') == fields.get('start_date')]
        result = {'id': candidate['id'], 'evidence': candidate['evidence']}
        if len(matches) != 1:
            result.update(status='missing-or-ambiguous; review required', matches=len(matches))
        else:
            index, row = matches[0]
            used.add(index)
            differences = [key for key, value in fields.items() if row.get(key) != value]
            result.update(status='field-differences; review required' if differences else 'exact-reviewed-fields',
                          differing_fields=differences)
        scores.append(result)
    return {'candidates': scores, 'unmatched_output_indices': [i for i in range(len(rows)) if i not in used],
            'accepted_listing_count': None,
            'note': 'Exact field checks only; resolve aliases, exclusions and semantic differences with source review'}


def replay(directory, output, generator, configure=None):
    report = {'database_access': False, 'publishing': False, 'samples': [],
              'cost_basis': 'Configured standard rates; uncached-input estimate, not a billing receipt',
              'upstream_run_id': os.environ.get('UPSTREAM_RUN_ID'), 'settings': generator.settings,
              'variant': os.environ.get('SHADOW_VARIANT', 'openai-non-reasoning')}
    output.mkdir(parents=True, exist_ok=True)
    report['capture_count'] = len(list(directory.rglob('sample-*.json')))
    report['unselected_count'] = max(0, report['capture_count'] - 4)
    try:
        for prefix in ('BASELINE', 'SHADOW'):
            estimate({'prompt_tokens': 0, 'output_tokens': 0}, prefix)
        failures = []
        for path, snapshot in select_samples(directory):
            prompt = snapshot['prompt']
            if not isinstance(prompt, str) or len(prompt) > 70000:
                raise ValueError('Captured prompt outside bounded review size')
            if not isinstance(snapshot['raw'], list) or not all(isinstance(x, dict) for x in snapshot['raw']):
                raise ValueError('Invalid baseline result')
            # Do not repeatedly pay to replay inputs already known to exceed the
            # output cap. Chunk preparation is offline and requires source review.
            visible_tokens = (snapshot['usage'].get('output_tokens', 0)
                              - snapshot['usage'].get('thinking_tokens', 0))
            output_cap = generator.settings.get('max_output_tokens', 0)
            if output_cap and visible_tokens > output_cap:
                report['samples'].append({'worker': snapshot['worker'],
                    'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                    'status': 'needs-reviewed-chunks; no paid request',
                    'baseline_visible_tokens': visible_tokens, 'output_cap': output_cap})
                continue
            if configure is not None and not configure(snapshot, generator):
                report['samples'].append({'worker': snapshot['worker'],
                    'baseline_settings': snapshot['settings'], 'status': 'unsupported-model; no paid request'})
                continue
            before = dict(generator.metrics)
            try:
                raw = generator.generate(prompt, snapshot['schema'])
            except Exception as exc:
                # Preserve the paid attempt and its identity without copying arbitrary
                # exception text, credentials, URLs or a partial rejected response.
                report['samples'].append({'worker': snapshot['worker'],
                    'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                    'baseline_settings': snapshot['settings'],
                    'baseline_usage': snapshot['usage'],
                    'shadow_settings': dict(generator.settings),
                    'shadow_usage': {k: v - before.get(k, 0) for k, v in generator.metrics.items()},
                    'status': 'failed; no retry or fallback',
                    'error_type': type(exc).__name__,
                    'diagnostics': exc.diagnostics if isinstance(exc, IncompleteOutputError) else None,
                    'comparison': None})
                # Billing/config, transport uncertainty and budget exhaustion stop
                # globally. Only content rejection may move to a different sample.
                if isinstance(exc, ValueError):
                    failures.append(type(exc).__name__)
                    continue
                raise
            usage = {k: v - before.get(k, 0) for k, v in generator.metrics.items()}
            report['samples'].append({'worker': snapshot['worker'],
                'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                'baseline_settings': snapshot['settings'], 'baseline_usage': snapshot['usage'],
                'shadow_settings': dict(generator.settings),
                'shadow_usage': usage, 'baseline_estimated_usd': estimate(snapshot['usage'], 'BASELINE'),
                'shadow_estimated_usd': estimate(usage, 'SHADOW'),
                'reference': snapshot.get('reference', {'kind': 'unreviewed-production-output'}),
                'source_score': score_reference(snapshot.get('reference', {}), raw),
                'comparison': compare(snapshot['raw'], raw), 'baseline_raw': snapshot['raw'], 'shadow_raw': raw})
        report['content_failures'] = len(failures)
        report['coverage_status'] = ('incomplete; review required' if failures or report['unselected_count'] or any(
            s.get('status') for s in report['samples']) else 'completed; quality review required')
    except Exception as exc:
        report['stopped'] = type(exc).__name__ + '; no retry or fallback'
        raise
    finally:
        report['metrics'] = dict(generator.metrics)
        (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    cohort = os.environ.get('SHADOW_REVIEWED_COHORT', '')
    if cohort and not re.fullmatch(r'artefacts/shadow-cohorts/[A-Za-z0-9_-]+', cohort):
        raise ValueError('Reviewed cohort must be a named directory under artefacts/shadow-cohorts')
    directory = Path(cohort or 'shadow-input')
    paths = list(directory.rglob('sample-*.json'))
    if cohort and (not paths or any(json.loads(p.read_text(encoding='utf-8')).get(
            'reference', {}).get('kind') != 'human-reviewed-source' for p in paths)):
        raise ValueError('Manual cohort requires prepared source-reviewed samples')
    if not paths:
        Path('shadow-results').mkdir(exist_ok=True)
        Path('shadow-results/results.json').write_text(json.dumps({'samples': [], 'reason': 'No successful captured Gemini calls; no shadow API calls'}))
    else:
        generator = StructuredGenerator('EXTRACTION', 'gemini-3.6-flash', 90)
        try:
            configure = configure_minimum if os.environ.get('SHADOW_VARIANT') == 'gemini-minimum-thinking' else None
            replay(directory, Path('shadow-results'), generator, configure)
            report = json.loads(Path('shadow-results/results.json').read_text(encoding='utf-8'))
            if report.get('content_failures') or any(s.get('status') for s in report['samples']):
                sys.exit(1)
        finally:
            generator.close()

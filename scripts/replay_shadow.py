"""Replay bounded captured prompts with OpenAI. Has no database or publisher code."""
import hashlib
import json
import math
import os
import re
from difflib import SequenceMatcher
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


# Owner-approved ceilings for a manual reviewed-cohort dispatch (#145, 23 Oct 2026). The automatic
# shadow keeps its defaults: 4 samples, 60k tokens, 3,000 output tokens.
CEILINGS = {'SHADOW_MAX_SAMPLES': 16, 'LLM_RUN_MAX_ATTEMPTS': 16,
            'LLM_RUN_TOKEN_BUDGET': 250_000, 'LLM_MAX_OUTPUT_TOKENS': 8_000}


def max_samples():
    value = int(os.environ.get('SHADOW_MAX_SAMPLES') or 4)
    if not 1 <= value <= CEILINGS['SHADOW_MAX_SAMPLES']:
        raise ValueError('SHADOW_MAX_SAMPLES must be 1-16')
    return value


def check_ceilings():
    for name, ceiling in CEILINGS.items():
        value = os.environ.get(name)
        if value and not 0 < int(value) <= ceiling:
            raise ValueError(f'{name} must be between 1 and {ceiling}')


def select_samples(directory):
    """Interleave workers before spending; one worker cannot take every slot."""
    limit = max_samples()
    groups = {}
    for path in sorted(directory.rglob('sample-*.json')):
        if path.stat().st_size > 500_000:
            raise ValueError('Capture outside bounded artifact size')
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        groups.setdefault(snapshot['worker'], []).append((path, snapshot))
    selected = []
    while any(groups.values()) and len(selected) < limit:
        for worker in sorted(groups):
            if groups[worker] and len(selected) < limit:
                selected.append(groups[worker].pop(0))
    return selected


def _text(value):
    value = str(value or '').casefold().replace('’', "'").replace('&', ' and ')
    return ' '.join(re.sub(r'[^\w\s\'½]', ' ', value).split())


def _url(value):
    value = str(value or '').strip()
    return re.sub(r'[?#].*$', '', value).rstrip('/').lower()  # query strings vary between runs


def _postcode(value):
    return re.sub(r'\s+', '', str(value or '')).upper()


def _similar(a, b, threshold=0.85):
    a, b = _text(a), _text(b)
    if not a or not b:
        return False
    return (len(min(a, b, key=len)) >= 6 and (a in b or b in a)) or SequenceMatcher(None, a, b).ratio() >= threshold


def _field_ok(key, expected, row):
    got = row.get(key)
    if expected is None:
        return got in (None, '', [])
    if key in ('start_date', 'end_date'):
        return str(got or '')[:10] == expected
    if key == 'event_url':
        return _url(got) == _url(expected)
    if key == 'postcode':  # a postcode is right if the output carries it anywhere in its location fields
        return _postcode(expected) in _postcode(' '.join(str(row.get(k) or '') for k in ('postcode', 'venue_address', 'location')))
    if key == 'title':
        return _similar(got, expected)
    if key == 'venue_name':
        return any(_similar(row.get(k), expected, 0.8) for k in ('venue_name', 'location', 'venue_address'))
    if key == 'age_range':  # "4 years to 12 years" and "4-12" are the same range
        numbers = lambda v: re.findall(r'\d+(?:\.\d+)?|½', str(v or ''))
        return bool(numbers(expected)) and numbers(got) == numbers(expected)
    return _text(got) == _text(expected)


def _identity(fields, row):
    """How strongly an output row is the referenced record; None when it cannot be."""
    if fields.get('event_url') and _url(row.get('event_url')) == _url(fields['event_url']):
        score = 3
    elif fields.get('title') and _similar(row.get('title'), fields['title']):
        score = 1
    else:
        return None
    for key in ('venue_name', 'postcode', 'start_date'):
        if fields.get(key):
            if _field_ok(key, fields[key], row):
                score += 1
            elif row.get(key) and key != 'venue_name':
                return None  # a different explicit date or postcode is a different record
    return score


def score_reference(reference, rows):
    """Identity-aware scoring against the source-reviewed reference; ambiguity stays a review item.

    Records pair one-to-one: by URL where the reference has one, otherwise by fuzzy title
    plus any listed venue, postcode or date. Only the fields a reference lists are scored.
    """
    if reference.get('kind') != 'source-reviewed':
        return None
    expected = reference['expected']
    pairs = sorted(((score, -e, -r) for e, candidate in enumerate(expected) for r, row in enumerate(rows)
                    if isinstance(row, dict) and (score := _identity(candidate['fields'], row)) is not None), reverse=True)
    matched, used = {}, set()
    for _, e, r in pairs:
        if -e not in matched and -r not in used:
            matched[-e] = -r
            used.add(-r)
    scores, checked, correct, typed, typed_ok = [], 0, 0, 0, 0
    for e, candidate in enumerate(expected):
        result = {'id': candidate['id'], 'evidence': candidate['evidence']}
        if e not in matched:
            result.update(status='missing; review required', differing_fields=None)
        else:
            row = rows[matched[e]]
            differences = [key for key, value in candidate['fields'].items() if not _field_ok(key, value, row)]
            checked += len(candidate['fields'])
            correct += len(candidate['fields']) - len(differences)
            if 'listing_type' in candidate['fields']:
                typed += 1
                typed_ok += 'listing_type' not in differences
            result.update(status='field-differences; review required' if differences else 'reviewed-fields-match',
                          output_index=matched[e], differing_fields=differences)
        scores.append(result)
    unmatched = [i for i in range(len(rows)) if i not in used]
    excluded_returned = [{'id': item['id'], 'output_index': i, 'reason': item['reason']}
                         for item in reference.get('excluded', []) for i in unmatched
                         if isinstance(rows[i], dict) and _similar(rows[i].get('title'), item['evidence'], 0.75)]
    flagged = {x['output_index'] for x in excluded_returned}
    return {'candidates': scores, 'unmatched_output_indices': unmatched,
            'excluded_returned': excluded_returned,
            'extra_output_indices': [i for i in unmatched if i not in flagged],
            'summary': {'expected': len(expected), 'matched': len(matched), 'fields_checked': checked,
                        'fields_correct': correct, 'classification_checked': typed, 'classification_correct': typed_ok,
                        'excluded_returned': len(excluded_returned), 'extras': len(unmatched) - len(flagged)},
            'accepted_listing_count': None,
            'note': 'Scored against AI-drafted references the owner spot-checked; review misses, extras and '
                    'returned exclusions against the source text before drawing conclusions'}


def replay(directory, output, generator, configure=None):
    report = {'database_access': False, 'publishing': False, 'samples': [],
              'cost_basis': 'Configured standard rates; uncached-input estimate, not a billing receipt',
              'upstream_run_id': os.environ.get('UPSTREAM_RUN_ID'), 'settings': generator.settings,
              'variant': os.environ.get('SHADOW_VARIANT', 'openai-non-reasoning')}
    output.mkdir(parents=True, exist_ok=True)
    report['capture_count'] = len(list(directory.rglob('sample-*.json')))
    report['unselected_count'] = max(0, report['capture_count'] - max_samples())
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
        summaries = [s['source_score']['summary'] for s in report['samples'] if (s.get('source_score') or {}).get('summary')]
        if summaries:
            report['score_summary'] = {key: sum(x[key] for x in summaries) for key in summaries[0]}
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
    check_ceilings()
    cohort = os.environ.get('SHADOW_REVIEWED_COHORT', '')
    if cohort and not re.fullmatch(r'artefacts/shadow-cohorts/[A-Za-z0-9_-]+', cohort):
        raise ValueError('Reviewed cohort must be a named directory under artefacts/shadow-cohorts')
    directory = Path(cohort or 'shadow-input')
    paths = list(directory.rglob('sample-*.json'))
    if cohort and (not paths or any(json.loads(p.read_text(encoding='utf-8')).get(
            'reference', {}).get('kind') != 'source-reviewed' for p in paths)):
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

"""Offline preparation of reviewed complete source chunks. Makes no API calls."""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(capture, manifest, output):
    prompt = capture['prompt']
    header, marker, source = prompt.partition('\nCONTENT:\n')
    if not marker:
        raise ValueError('Capture has no unambiguous content boundary')
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    if manifest.get('prompt_sha256') != digest or not manifest.get('reviewer', '').strip():
        raise ValueError('Manifest requires matching prompt hash and named reviewer')
    chunks = manifest.get('chunks', [])
    if not chunks or len(chunks) > 100:
        raise ValueError('Require 1–100 reviewed chunks')
    position, prepared = 0, []
    for index, chunk in enumerate(chunks):
        start, end = chunk['start'], chunk['end']
        if type(start) is not int or type(end) is not int or start != position or not start < end <= len(source):
            raise ValueError('Spans must partition the entire source without gaps or overlaps')
        if chunk.get('complete_records') is not True:
            raise ValueError('Reviewer must confirm boundaries preserve complete records')
        text = source[start:end]
        chunk_prompt = header + marker + text
        if len(chunk_prompt) > 14000:
            raise ValueError('Reviewed chunk prompt exceeds 14,000 characters')
        expected = chunk.get('expected', [])
        excluded = chunk.get('excluded', [])
        if not isinstance(expected, list) or not isinstance(excluded, list):
            raise ValueError('Expected/excluded must be lists')
        ids = set()
        for item in expected + excluded:
            if not item.get('id') or item['id'] in ids or not item.get('evidence') or item['evidence'] not in text:
                raise ValueError('Each candidate needs a unique ID and exact source evidence')
            ids.add(item['id'])
            if item in expected and not isinstance(item.get('fields'), dict):
                raise ValueError('Expected candidates require reviewed fields')
            if item in excluded and not item.get('reason'):
                raise ValueError('Excluded candidates require a reason')
        if chunk.get('all_candidates_reviewed') is not True:
            raise ValueError('Reviewer must reconcile every candidate, including exclusions')
        prepared.append({'worker': capture['worker'], 'prompt': chunk_prompt,
            'schema': capture['schema'], 'settings': capture['settings'],
            'raw': [item['fields'] for item in expected], 'usage': {},
            'reference': {'kind': 'source-reviewed', 'reviewer': manifest['reviewer'],
                'reviewer_type': manifest.get('reviewer_type', 'unspecified'),
                'parent_prompt_sha256': digest, 'chunk_index': index,
                'source_start': start, 'source_end': end, 'source_chars': len(source),
                'expected': expected, 'excluded': excluded,
                'baseline_cost_comparable': False}})
        position = end
    if position != len(source):
        raise ValueError('Manifest omits the end of the source')
    # Validate the entire manifest before creating any files; never overwrite a cohort.
    output.mkdir(parents=True, exist_ok=False)
    for index, sample in enumerate(prepared):
        (output / f'sample-{index + 1:03}.json').write_text(
            json.dumps(sample, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'coverage.json').write_text(json.dumps({
        'parent_prompt_sha256': digest, 'source_chars': len(source),
        'chunk_count': len(prepared), 'reviewer': manifest['reviewer'],
        'expected_candidates': sum(len(x['raw']) for x in prepared),
        'excluded_candidates': sum(len(x['reference']['excluded']) for x in prepared),
        'replayed': False, 'cost_comparison': 'unavailable; full-source baseline not comparable'},
        indent=2), encoding='utf-8')
    return prepared


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    prepare(json.loads(args.capture.read_text(encoding='utf-8')),
            json.loads(args.manifest.read_text(encoding='utf-8')), args.output)

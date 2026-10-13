"""Compare saved HTML preparation against a git baseline, without AI or DB calls.

Usage: python scripts/measure_extraction_input.py SNAPSHOT_DIR --baseline REF
Each snapshot is JSON containing `url` and `documents` (URL/HTML pairs).
Prints character counts only: these are not billed-token or quality measurements.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import worker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshots', type=Path)
    parser.add_argument('--baseline', default='772a0754f8160113fce30533f8ce3ad086e98b73')
    args = parser.parse_args()
    code = subprocess.check_output(['git', 'show', args.baseline + ':worker.py'], cwd=ROOT).decode('utf-8')
    old = {'__name__': 'baseline_worker'}
    exec(compile(code, '<baseline worker>', 'exec'), old)
    results = []
    for path in sorted(args.snapshots.glob('*.json')):
        snapshot = json.loads(path.read_text(encoding='utf-8'))
        docs = snapshot['documents']
        url = snapshot['url']
        before, _ = old['prepare_content'](docs, url)
        after, _ = worker.prepare_content(docs, url)
        results.append({'source': path.stem, 'url': url,
                        'snapshot_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'before_chars': len(before), 'after_chars': len(after),
                        'reduction_chars': len(before) - len(after),
                        'after_at_limit': len(after) >= worker.MAX_CHARS})
    if not results:
        parser.error('no saved JSON snapshots found')
    print(json.dumps({'baseline': args.baseline, 'measure': 'prepared characters, not tokens',
                      'max_chars': worker.MAX_CHARS, 'sources': results}, indent=2))


if __name__ == '__main__':
    main()

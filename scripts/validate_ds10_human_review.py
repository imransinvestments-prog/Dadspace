"""Validate returned human review answers; never write to production or close issues."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def validate(sample,review):
    expected={r['id'] for r in sample['rows']}
    answers=review.get('answers',{})
    errors=[]
    if len(expected)!=100 or set(answers)!=expected:
        errors.append('Exactly the 100 sampled IDs must be reviewed; missing or extra IDs are not accepted')
    if review.get('sample')!='ds10-human-review-2026-10-11.json' or review.get('reviewer')!='Imran Tajuddin':
        errors.append('Sample/reviewer does not match the agreed review')
    if not review.get('reviewed_at'): errors.append('Missing review timestamp')
    for id in expected:
        if any(answers.get(id,{}).get(k) not in ('yes','no') for k in ('relevant','current','actionable')):
            errors.append('Incomplete review: '+id)
    passed=sum(all(answers.get(id,{}).get(k)=='yes' for k in ('relevant','current','actionable')) for id in expected)
    return dict(sample_count=len(expected),passed=passed,failed=len(expected)-passed,
                complete=not errors,quality_target_met=not errors and passed>=90,errors=errors,
                other_acceptance='Pilot breadth, source access, scheduled repeats and release gates require separate evidence')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('review',type=Path)
    args=parser.parse_args()
    sample=json.loads((ROOT/'artefacts/data/ds10-human-review-2026-10-11.json').read_text(encoding='utf-8'))
    report=validate(sample,json.loads(args.review.read_text(encoding='utf-8')))
    print(json.dumps(report,indent=2))
    if not report['quality_target_met']: raise SystemExit(1)

if __name__=='__main__': main()

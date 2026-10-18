"""Rebuild #182 from a frozen SQL snapshot and frozen postcode response; no network."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from activity_eligibility import build_ledger

parser=argparse.ArgumentParser()
parser.add_argument('snapshot')
parser.add_argument('postcodes')
parser.add_argument('output')
args=parser.parse_args()
snapshot=json.loads(Path(args.snapshot).read_text(encoding='utf-8'))
postcodes=json.loads(Path(args.postcodes).read_text(encoding='utf-8'))
ledger=build_ledger(snapshot,postcodes['results'])
Path(args.output).write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:value for key,value in ledger.items() if key!='rows'},ensure_ascii=False,indent=2))

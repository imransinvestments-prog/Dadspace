"""PostToolUse: after a Python edit, run tests/test_<module>.py the same way CI does."""
import json
import os
import subprocess
import sys
from pathlib import Path

event = json.loads(sys.stdin.buffer.read() or b'{}')
target = (event.get('tool_input') or {}).get('file_path') or ''
if not target.endswith('.py'):
    sys.exit(0)

root = Path(os.environ.get('CLAUDE_PROJECT_DIR') or event.get('cwd') or '.').resolve()
path = Path(target)
path = (path if path.is_absolute() else root / path).resolve()
if 'Archived' in path.parts or '.claude' in path.parts:
    sys.exit(0)

test_name = path.name if path.name.startswith('test_') else f'test_{path.name}'
if not (root / 'tests' / test_name).exists():
    sys.exit(0)

try:
    result = subprocess.run(
        [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', test_name],
        cwd=root, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=150)
except subprocess.TimeoutExpired:
    print(f'tests/{test_name} timed out after 150s', file=sys.stderr)
    sys.exit(2)

if result.returncode != 0:
    output = (result.stdout + result.stderr).strip()
    if 'ModuleNotFoundError' in output:
        # A local environment gap, not a code failure: warn without blocking.
        print(f'Skipped tests/{test_name}: missing Python dependency. '
              'Run: pip install -r requirements.txt', file=sys.stderr)
        sys.exit(1)
    print(f'tests/{test_name} failed after editing {path.name}:\n{output[-4000:]}', file=sys.stderr)
    sys.exit(2)

"""PostToolUse: after a .ts/.tsx edit, run tsc --noEmit (the check CI runs before build)."""
import json
import os
import subprocess
import sys
from pathlib import Path

event = json.loads(sys.stdin.buffer.read() or b'{}')
target = (event.get('tool_input') or {}).get('file_path') or ''
if not target.endswith(('.ts', '.tsx')):
    sys.exit(0)

root = Path(os.environ.get('CLAUDE_PROJECT_DIR') or event.get('cwd') or '.').resolve()
tsc = root / 'node_modules' / 'typescript' / 'bin' / 'tsc'
if not tsc.exists():
    # Dependencies are not installed locally; CI still type-checks.
    sys.exit(0)

try:
    result = subprocess.run(['node', str(tsc), '--noEmit', '--pretty', 'false'], cwd=root,
                            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=170)
except subprocess.TimeoutExpired:
    print('tsc --noEmit timed out after 170s', file=sys.stderr)
    sys.exit(2)

if result.returncode != 0:
    # Archived/ is untracked local material that tsconfig's **/* glob picks up; CI never sees it.
    errors = [line for line in (result.stdout + result.stderr).splitlines()
              if 'error TS' in line and not line.replace('\\', '/').startswith('Archived/')]
    if errors:
        output = '\n'.join(errors)
        print(f'tsc --noEmit failed:\n{output[-4000:]}', file=sys.stderr)
        sys.exit(2)

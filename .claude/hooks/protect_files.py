"""PreToolUse guard: block edits to lockfiles, env files and applied migrations."""
import json
import os
import sys
from pathlib import Path

event = json.loads(sys.stdin.buffer.read() or b'{}')
target = (event.get('tool_input') or {}).get('file_path') or ''
if not target:
    sys.exit(0)

root = Path(os.environ.get('CLAUDE_PROJECT_DIR') or event.get('cwd') or '.').resolve()
path = Path(target)
path = (path if path.is_absolute() else root / path).resolve()
name = path.name.lower()

reason = ''
if name == 'pnpm-lock.yaml':
    reason = 'pnpm-lock.yaml is generated; change package.json and run pnpm install instead.'
elif name.startswith('.env') and name != '.env.example':
    reason = f'{path.name} holds secrets and must be edited by hand.'
else:
    try:
        relative = path.relative_to(root).as_posix().lower()
    except ValueError:
        relative = ''
    # New migrations are fine; rewriting one that may already be applied is not.
    if relative.startswith('supabase/migrations/') and path.exists():
        reason = (f'{path.name} is an existing migration and may already be applied. '
                  'Add a new timestamped migration instead.')

if reason:
    print(f'Blocked: {reason}', file=sys.stderr)
    sys.exit(2)

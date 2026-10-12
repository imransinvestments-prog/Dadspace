"""Optional disposable result cache; source persistence owns the commit boundary."""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path


class ResultCache:
    def __init__(self, directory, refresh_days=7):
        self.directory = Path(directory)
        self.refresh_days = refresh_days
        self.pending = {}

    def path(self, source_id, page_url):
        key = hashlib.sha256((str(source_id) + '\n' + page_url).encode()).hexdigest()
        return self.directory / (key + '.json')

    def get(self, source_id, page_url, digest, today):
        if self.refresh_days <= 0:
            return None
        path = self.path(source_id, page_url)
        try:
            if path.stat().st_size > 2_000_000:
                return None
            entry = json.loads(path.read_text(encoding='utf-8'))
            age = (today - dt.date.fromisoformat(entry['extracted_at'])).days
            raw = entry['raw']
            if (entry['digest'] != digest or not 0 <= age < self.refresh_days
                    or not isinstance(raw, list) or not all(isinstance(x, dict) for x in raw)):
                return None
            return raw
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def stage(self, source_id, page_url, digest, today, raw):
        # Never persist credentials or source HTML; only public extraction results.
        entry = {'digest': digest, 'extracted_at': today.isoformat(), 'raw': raw}
        self.pending.setdefault(str(source_id), {})[self.path(source_id, page_url)] = entry

    def discard(self, source_id):
        self.pending.pop(str(source_id), None)

    def commit(self, source_id):
        entries = self.pending.pop(str(source_id), {})
        if not entries:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        for path, entry in entries.items():
            temp = path.with_suffix('.tmp')
            temp.write_text(json.dumps(entry, ensure_ascii=False), encoding='utf-8')
            temp.replace(path)
        # This is disposable public result data, not an archive. Bound historical
        # detail URLs; old entries become ordinary misses after removal.
        today = dt.date.fromisoformat(next(iter(entries.values()))['extracted_at'])
        for path in self.directory.glob('*.json'):
            if not re.fullmatch(r'[a-f0-9]{64}\.json', path.name):
                continue
            try:
                entry = json.loads(path.read_text(encoding='utf-8'))
                if (today - dt.date.fromisoformat(entry['extracted_at'])).days >= max(1, self.refresh_days):
                    path.unlink()
            except (OSError, ValueError, KeyError, TypeError):
                continue

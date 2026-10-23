"""Rebuild shadow captures offline from public source pages. No model call, no database.

python scripts/rebuild_shadow_captures.py sources.json events-civic OUTPUT_DIRECTORY

Runs the collector's own path for each source (robots check, fetch, page preparation
and build_prompt) with the production environment of that worker, but the extract
step records the prompt instead of calling Gemini. Output files match shadow_capture.py
captures, with raw=[] (there is no production response) and settings marking the rebuild,
so scripts/prepare_shadow_chunks.py can turn them into reviewed chunks.
"""
import datetime as dt
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# The collectors' production settings (collect-civic.yml, collect-activities.yml).
WORKERS = {
    'events-civic': {'CATEGORIES': 'councils,heritage_parks,niche_venues', 'FETCH_ENGINE': 'requests'},
    'events-activities': {'CATEGORIES': 'activities', 'FETCH_ENGINE': 'browser', 'MAX_CHARS': '24000',
                          'BROWSER_GOTO_TIMEOUT_MS': '30000', 'BROWSER_SETTLE_MS': '2500'},
}


def main():
    sources_path, worker, output = sys.argv[1:4]
    # worker.py reads these at import, so they must be set first. No database secrets are used.
    os.environ.update(WORKERS[worker], WORKER_NAME=worker, DRY_RUN='true', EXTRACTION_PER_PAGE='false')
    for name in ('SUPABASE_URL', 'SUPABASE_KEY', 'GEMINI_API_KEY', 'EXTRACTION_CACHE_DIR', 'SHADOW_CAPTURE_DIR'):
        os.environ.pop(name, None)
    import gemini_usage
    import events_worker
    from pydantic import TypeAdapter
    events_worker.install_quality_rules()
    base = events_worker.base

    # The exact response schema production sends, without building a Gemini client.
    captured, original = {}, gemini_usage.make_extractor
    gemini_usage.make_extractor = lambda model, schema, timeout, fatal: captured.setdefault('schema', TypeAdapter(schema).json_schema())
    try:
        events_worker.make_gemini_caller()
    finally:
        gemini_usage.make_extractor = original

    today = dt.date.today()
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    for source in json.loads(Path(sources_path).read_text(encoding='utf-8')):
        prompts = []
        def extract(prompt):
            prompts.append(prompt)
            return []
        extract.metrics, extract.settings, extract.close = {}, {}, lambda: None
        # A rebuild always re-reads: the stored hash would otherwise short-circuit as unchanged.
        status, _, _, message, _ = base.process_source(dict(source, last_hash=None, last_success_at=None), extract, today)
        slug = ''.join(c if c.isalnum() else '-' for c in source['name'].lower()).strip('-')
        print(f'{source["name"]}: {status}; {len(prompts)} prompt(s); {message[:120]}')
        for index, prompt in enumerate(prompts, 1):
            capture = {'worker': worker, 'prompt': prompt, 'schema': captured['schema'], 'raw': [], 'usage': {},
                       'settings': {'provider': 'gemini', 'model': base.MODEL, 'rebuilt_offline': True,
                                    'rebuilt_on': today.isoformat(), 'fetch_engine': base.FETCH_ENGINE},
                       'source': {k: source.get(k) for k in ('id', 'name', 'url', 'category', 'nation', 'region')}}
            (out / f'{slug}-{index}.json').write_text(json.dumps(capture, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()

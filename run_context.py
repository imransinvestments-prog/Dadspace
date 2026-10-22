"""Shared run evidence for pipeline_runs.details.

Job logs need authentication even on a public repository, so a failed scheduled
run must be explainable from the database row alone: which GitHub run wrote it,
what the worker concluded and why. Keys match collection_evidence.py.
"""
import datetime as dt
import os

MAX_LISTED = 25


def github_run():
    return {key: os.environ.get(name) for key, name in (
        ('run_id', 'GITHUB_RUN_ID'), ('attempt', 'GITHUB_RUN_ATTEMPT'),
        ('sha', 'GITHUB_SHA'), ('event', 'GITHUB_EVENT_NAME'),
        ('workflow', 'GITHUB_WORKFLOW'), ('job', 'GITHUB_JOB'))}


def run_details(status, reasons=(), failed=(), **extra):
    """status is ok, degraded or failed; reasons say why it is not ok."""
    if status not in ("ok", "degraded", "failed"):
        raise ValueError(f"unknown run status {status!r}")
    failed = [str(item)[:200] for item in failed]
    return {"status": status, "reasons": list(reasons), "failed_sources": failed[:MAX_LISTED],
            "failed_source_count": len(failed), "github": github_run(),
            "logged_at": dt.datetime.now(dt.timezone.utc).isoformat(), **extra}

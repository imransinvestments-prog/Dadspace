"""Resolve Google News wrappers before storing article links."""
from urllib.parse import urlsplit
import time
import requests
from googlenewsdecoder._parse import (
    article_id, parse_signature, build_batchexecute_body, parse_batchexecute,
)


def is_google_news(url):
    return urlsplit(url or "").hostname == "news.google.com"


def publisher_url(url):
    """Only accept complete HTTP(S) article URLs outside Google's services."""
    try:
        parts = urlsplit(url or "")
        host = (parts.hostname or "").lower()
        if parts.scheme not in ("http", "https") or not host or parts.username or parts.password:
            return None
        if host == "google.com" or host.endswith(".google.com") or host == "googleusercontent.com" or host.endswith(".googleusercontent.com"):
            return None
        return url
    except ValueError:
        return None


def resolve_article_urls(urls):
    """Return verified destinations; failures preserve the original link."""
    resolved = list(urls)
    pending = [(i, url) for i, url in enumerate(urls) if is_google_news(url)]
    for start in range(0, len(pending), 20):
        batch = pending[start:start + 20]
        try:
            pending = []
            with requests.Session() as session:
                for i, url in batch:
                    try:
                        response = session.get(url, timeout=10)
                        response.raise_for_status()
                        signature = parse_signature(response.text)
                        if signature:
                            sg, ts = signature
                            pending.append((str(i), article_id(url), ts, sg))
                    except (requests.RequestException, ValueError):
                        pass
                    time.sleep(0.2)
                if not pending:
                    continue
                response = session.post(
                    "https://news.google.com/_/DotsSplashUi/data/batchexecute",
                    data=build_batchexecute_body(pending),
                    headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                    timeout=10,
                )
                response.raise_for_status()
                targets = dict(parse_batchexecute(response.text))
                results = [{"success": str(i) in targets, "decoded_url": targets.get(str(i))}
                           for i, _ in batch]
        except Exception:
            continue
        if not isinstance(results, list) or len(results) != len(batch):
            continue
        for (i, _), result in zip(batch, results):
            target = publisher_url(result.get("decoded_url")) if result.get("success") else None
            if target:
                resolved[i] = target
    return resolved

# Homepage newspaper — issue #61

Testing branch: `codex/mvp-testing`. The Dad Space Times replaces the homepage headline grid with a responsive parchment newspaper, nine real category sections, outlined icons, exact monthly counts, and category links.

Counts include relevance >= 3 and primary (or legacy null primary) news records first ingested during the current Europe/London calendar month. They use exact HEAD counts against the existing server-only `news_items` read path, not a limited page of `feed_items`. The server service key remains private. Missing server credentials and query failures display unavailable counts; a successful empty month displays zero. Results are cached for ten minutes and keyed by month. The homepage's existing minute refresh picks up refreshed counts.

Live schema inspection on 9 October verified `feed_items` retains its rolling 14-day public feed. Links select the requested category in SSR and hydration; the newspaper footer explains that section results cover the latest fortnight. Other news is now selectable. Invalid/multiple category parameters fall back to All. No database policies, tables or production deployment changed.

Worker retention is at least 35 days, including when a shorter RETENTION_DAYS value is configured, so future collection preserves a complete 31-day month. Previously deleted records cannot be recovered by this change. The earliest retained record on verification was 30 September, so the current October month was covered.

Validation: TypeScript; three monthly count/calendar/error regression tests; existing news locality/category/pagination regression suite; 16 deals-selection regression tests. The local Windows sandbox prevents native SWC from canonicalizing the checkout, so the full build must be confirmed by the testing branch's Linux GitHub Actions job. Browser connectivity also prevented localhost visual QA; a static preview was generated from the actual React component and Tailwind utilities using the live count snapshot.

Rollback: revert the issue #61 commit on the testing branch. No schema rollback is required.

# Dadspace Originals (#63)

The `/originals` hub supports daily/weekly filters and links to `/originals/[slug]` articles. Desktop and mobile navigation expose it. The core sitemap lists the hub and 60 most recent articles. Older articles keep their URLs; the hub displays the 60 newest per selected cadence. Content pages read Supabase on each request, so publication does not require a deploy.

## Publishing

`.github/workflows/original-content.yml` runs at 07:17 and 09:17 Europe/London daily (DST aware). GitHub may delay scheduled jobs. The later run retries failed slots without generating duplicates. `original_content_worker.py` publishes one daily tip per London calendar date and a longer guide on Fridays. The workflow must be on the default/main branch for schedules to run. It also runs on worker changes to main for immediate verification. Checks run without secrets on PRs; publishing only runs on main after checks.

Uses existing `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY` GitHub secrets. Default model matches the news worker, `gemini-3.5-flash`; set `ORIGINAL_CONTENT_MODEL` on the job to override. Typically two calls per new post (generation and editorial review): 16 calls/week. Existing slots spend no model calls. Timeouts fail the run; no unchecked fallback is published. Dry run validates without writing. No user or scraped content is passed to Gemini.

Practical, low-risk family ideas only. No medical/legal/financial advice, real-world venue claims, prices, current events, invented personal experience, quotes or product endorsements. Word count, schema, markup/link/placeholder and title-duplication gates precede a separate model editorial review. This automated review is not a human factual guarantee. Recent topics/titles guide variety; this is not a plagiarism detection service. Page copy discloses AI assistance.

`original_posts` has unique `(cadence,slot_date)` and slug keys. Inserts ignore duplicate slots, so simultaneous or repeated runs cannot overwrite a post. RLS and explicit grants allow public read of already published posts; only the service role writes. To withdraw a post, move `published_at` into the future; reads and sitemaps exclude it. Disable the workflow to pause automatic publication.

Run `python -m unittest discover -s tests -p test_original_content.py -v`, TypeScript, and the Next production build. Worker failures appear in GitHub Actions. The DB migration is recorded in Supabase as `original_posts`; SQL is also kept beside this document.

References: [GitHub scheduled events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output), [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).

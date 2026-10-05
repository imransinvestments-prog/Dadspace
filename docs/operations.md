# Dadspace operations

Updated 5 October 2026. Baseline: main commit `15fb332882494cefcc950136ee0ed798ef5105b7`.

## Configuration

Keep credential values in GitHub Actions secrets or hosting environment settings. This documentation lists variable names only.

| Consumer | Configuration |
| --- | --- |
| Generic events, activities, reference and NCT workflows | SUPABASE_URL, SUPABASE_KEY; Gemini settings where the workflow declares them |
| News workflow | SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY |
| Deals workflow | SUPABASE_URL; supported SUPABASE_SERVICE_ROLE_KEY / SUPABASE_SERVICE_KEY / SUPABASE_KEY aliases; Gemini and adapter-specific credentials |
| App listing server | NEXT_PUBLIC_DADSPACE_SUPABASE_URL, DADSPACE_SUPABASE_SERVICE_ROLE_KEY; anon fallback |
| News client | NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY or Dadspace-prefixed aliases |
| Venue photo server | GOOGLE_PLACES_API_KEY plus configured Supabase connection |
| Deals API adapters | AWIN_API_TOKEN, AWIN_PUBLISHER_ID, FMTC_API_TOKEN, PEPPER_API_KEY as applicable |

The workflow is the authority for each collector's exact accepted settings. A variable being declared does not mean the corresponding source is configured or active. Never put service-role or provider secret values in NEXT_PUBLIC variables.

## Review a collector change

1. Confirm the source role, category, adapter and active status, and choose the matching workflow.
2. Read its inputs and triggers. Use dry_run=true and a small limit where supported.
3. Inspect extraction decisions, rejected examples, duplicates, dates, schedules, addresses and venue relationships.
4. Review source failures and token/runtime metrics, not just total row count.
5. Before a live event write, confirm the workflow's backup step succeeded. Download its artifact.
6. After an authorised live run, check stored records and the app's read view/filter. Review new venue visibility separately.

The daily orchestrator requests live runs. NCT and reference push triggers also request live writes for matching code paths. A documentation-only update does not match those paths.

## Run diagnostics

- Start with GitHub Actions logs and artifacts; some workflows have offline self-tests, while others test real connections.
- For news/events/deals, inspect available pipeline_runs entries and source health alongside workflow results.
- If civic/activities/deals were skipped, inspect the preceding job in the daily dependency chain.
- An inactive source or repeated source failure can explain lost coverage.
- For missing activities, check listing_type and last_seen_at against current_activities.
- For missing venues, check public_visible, discovery_status, review_reason and any matching/provenance record.
- For missing news, check source ingestion, grouping/primary records and feed_items access.
- For missing deals, distinguish ingestion failures, relevance rejection, lifecycle expiry and page query filters.
- A holding page can conceal available app pages; COMING_SOON remains true in this baseline. API routes have separate access behaviour.

## Venue review

Use the restricted venues_to_review view through an authorised administrative connection. Check the facility's identity, exact location, source evidence, duplicates, category and suitability before publishing. Reference libraries follow a separate auto-publication path in loader v2; do not assume every visible venue passed human review.

Reference-loader labels such as hidden_or_existing and the workflow input description currently conflict with new library visibility. The code's public_visible=true assignment is the documented behaviour.

## Repository and deployment evidence

Migrations and SQL files describe intended database changes, not proof that every environment applied them. Before changing schema or access, inspect the deployed schema, grants and policies. In particular, server-role listing reads and anon news reads must be assessed independently.

Keep the public launch decision separate from collection health. Forum rooms and moderation need implementation and verification before launch.

## Documentation maintenance

Update these files when changing workflow entry points, scheduling, dependencies, tables/views, venue publication, credentials, read filters or launch status. Record a new baseline commit and distinguish merged code from proposed work. Keep downloadable bundles in sync with the committed Markdown.

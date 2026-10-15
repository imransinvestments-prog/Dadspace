# Visibility verification — 15 October 2026

The owner confirmed that playgrounds with missing access information are accessible to the public and requested restoration of their publication. That decision supersedes the earlier hold for missing access for playgrounds only.

## Verified production state

- 59,100 venue records retained; 56,745 publicly visible.
- All 37,145 playgrounds with missing/blank access are public; none remain hidden.
- Zero parks/playgrounds marked `private` or `no` are public.
- The 575 other park records with missing access (188 theme parks, 112 water parks and 275 animal parks) remain hidden.
- All 80 reviewed arcade exclusions remain hidden.
- An additional 129 discovered venues are now public: 37 libraries and 92 records without a category. These were not part of the playground restoration. This verification records the owner's database state without asserting independent suitability review of those 129 venues.

## Owner confirmation and database review safeguard

The restoration appends the owner's public-access confirmation to `review_reason`, sets `ops_reviewed_at`, and retains the imported `access` value and source evidence. The earlier hold remains in the audit history but is explicitly superseded.

The `venues_preserve_operations_review` trigger preserves previously reviewed fields during ordinary importer updates. Intentional review updates use `SET LOCAL dadspace.review_write='on'` within the transaction. A normal UPDATE without that setting can report matched rows while the trigger preserves the previous publication decision; always verify persisted values afterwards.

The historical restoration transaction is recorded in `artefacts/data/public-playground-restoration-2026-10-14.sql`. It is an audit artifact, not a migration or an automated publishing policy. Local before-change snapshots remain available for selective rollback.

## Code and live site

PR #105 was merged into main as `74b774cde93741792196637191a4e48022ad2966`. The subsequent main head checked for this audit was `fcd3e4f593feb6b7f3a5c857cbc7027845a91df6`, which contains that merge; its Vercel deployment is successful. All eight local implementation/audit files from that PR match main, disregarding line endings. No stale local reporting files were pushed over newer main-branch reports.

Live `/venues` returns HTTP 200 without Rainy-day proof or Outdoors controls; Free entry remains. `/events` labels both hero counts UK-wide. Issue #86 is closed with the owner's accepted resolution of removing the unsupported controls. The original evidenced indoor/outdoor capability work was not implemented; any future reinstatement needs a separate evidence-backed change.

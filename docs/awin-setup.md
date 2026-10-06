# AWIN setup and acceptance

This branch builds on `codex/mvp-testing` and preserves its canonical taxonomy,
shared public selection, rules-only collection, verification and health reports.
AWIN account access has not yet been tested. No source has been activated by this change.

1. Sign in at [API Credentials](https://ui.awin.com/awin-api). An account admin
   can obtain the personal API token following [AWIN authentication](https://help.awin.com/apidocs/api-authentication).
2. Add `AWIN_API_TOKEN` and `AWIN_PUBLISHER_ID` to
   [repository Actions secrets](https://github.com/imransinvestments-prog/Dadspace/settings/secrets/actions).
   Never put the token in Git, chat, frontend variables or URLs. The personal token
   can access every AWIN account associated with its user.
3. Run **Validate and enable Awin** with `activate=false`. It checks the complete
   paginated joined-programme, active GB promotions response without DB writes.
   An empty successful response proves access, not useful supply; join suitable UK
   advertiser programmes in AWIN and review their offers.
4. After access succeeds, run with `activate=true`. It enables the existing single
   AWIN source, confirms the saved state, and starts the normal live collector.
   Collection preserves codes, tracking links, terms and dates. Unsupported savings
   remain rejected. Inspect the review artifacts, health report and preview pool.
5. Repeat collection and human-label the published pool before accepting DS-07/08.
   Two scheduled runs and seven days of freshness observation remain outstanding.
   This workflow does not change the production launch gate or default-branch schedule.

## Publisher MasterTag

Set `AWIN_PUBLISHER_ID` in Vercel for the relevant preview/production environment
and rebuild. The root layout adds the script as the final body element when
the app is visible and the ID is valid. The coming-soon page has no affiliate links
and does not load the tag. Only the publisher ID enters the rendered script URL;
the API token is never used by the website.

Following [AWIN's installation guide](https://success.awin.com/s/article/what-is-publisher-mastertag?language=en_US),
check the browser Network tab for `dwin`, confirm the publisher ID and successful
script response, and verify placement before `</body>`. In AWIN, open **Toolbox →
Publisher MasterTag** to review permissions and activate the desired plugin.
Installing the script does not activate plugins. Review Tracking Optimisation
first; optional Convert-a-Link and other plugins require a separate account choice.

Rollback: set the AWIN source `active=false` to stop collection; remove the Vercel
publisher ID and rebuild to remove the tag. Preserve historical offers and evidence.

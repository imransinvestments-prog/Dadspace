# Dadspace technical documentation

For the current testing branch, start with the [8 October integration summary](mvp-testing-integration-2026-10-08.md). It records merged features and supersedes the older baseline statements below where testing differs.

Updated 5 October 2026. Code baseline: main commit `29275e17dab42804ecebec529dda2f596ea6cdc7`.

- [Architecture](architecture.md): application, collectors, database, access boundaries and launch state.
- [Worker roles](worker-roles.md): workflow entry points, responsibilities and scheduling.
- [Data flows](data-flows.md): ingestion, identity, venue discovery, publication and reads.
- [Operations](operations.md): configuration, previews, review and troubleshooting.
- [Google venue photos](venue-google-photos.md): matching, delivery and existing verification commands.

These documents describe committed code, not a live infrastructure audit. Repository migrations express intended schema; deployment, active source rows, credentials, policies and workflow health must be checked separately. Older chat diagrams should be read alongside this dated baseline.

Ongoing work on deals quality, activity coverage, venue validation and forum rooms is not assumed released. Refresh these documents when the corresponding changes merge.

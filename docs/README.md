# Dadspace technical documentation

Updated 5 October 2026. Code baseline: main commit `15fb332882494cefcc950136ee0ed798ef5105b7`.

- [Architecture](architecture.md): application, collectors, database, access boundaries and launch state.
- [Worker roles](worker-roles.md): workflow entry points, responsibilities and scheduling.
- [Data flows](data-flows.md): ingestion, identity, venue discovery, publication and reads.
- [Operations](operations.md): configuration, previews, review and troubleshooting.
- [Google venue photos](venue-google-photos.md): matching, delivery and existing verification commands.

These documents describe committed code, not a live infrastructure audit. Repository migrations express intended schema; deployment, active source rows, credentials, policies and workflow health must be checked separately. Older chat diagrams should be read alongside this dated baseline.

Ongoing work on deals quality, activity coverage, venue validation and forum rooms is not assumed released. Refresh these documents when the corresponding changes merge.

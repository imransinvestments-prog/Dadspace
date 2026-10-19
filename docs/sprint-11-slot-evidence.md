# Reviewed scheduled-slot evidence

The ledger reads optional `artefacts/data/sprint11-slot-evidence.json`. Absence preserves unknown attribution. This is a reviewed evidence index, not a generator of schedule success. Never choose a slot merely because it is closest to a run timestamp.

Use this envelope only after inspecting retained evidence which identifies the triggering occurrence:

```json
{
  "version": 1,
  "assignments": [
    {
      "workflow": "daily-workers.yml",
      "expected_at": "2026-10-18T06:17:00+00:00",
      "run_id": 123456789,
      "run_attempt": 1,
      "head_sha": "replace-with-the-exact-captured-40-character-SHA",
      "evidence_url": "https://example.org/retained/unique-occurrence-evidence",
      "reviewed_by": "actual reviewer identity",
      "reviewed_at": "2026-10-18T07:00:00+00:00"
    }
  ]
}
```

The example is illustrative and must not be copied as actual evidence. The run must exist in `sprint11-scheduled-runs.json` with the same workflow, run ID, attempt, SHA and scheduled event. Retain an accessible, unique evidence URL for each occurrence. Review timestamps must fall after the captured run started and before the capture cutoff. Unknown occurrence evidence stays absent. Conflicts, duplicate slots, reuse of a run (including another attempt) or evidence URL fail the complete input before any ledger write.

Run `python scripts/sprint11_schedule_ledger.py` to regenerate the ledger. Its fixed default window covers seven London calendar dates beginning 18 October; Python tests can supply another explicit start date, including a DST window. All input instants require timezone offsets.

`slot_coverage` becomes `met` only for 14 successful, stable-configuration, attributed slots per workflow. Dispatch after 60 minutes or captured run update after four hours from the intended slot fails that slot. The update timestamp is a conservative completion upper bound, explicitly named in output; no job completion time is invented. Incomplete, failed, late, mismatched, future and unattributed slots remain separate states.

`acceptance` remains `not_met` and `feed_publication_acceptance` remains `not_evaluated`: parent workflow coverage cannot establish individual feed eligibility, Activities collection counts, source freshness, publication identity/terms, Friday publication or failure/recovery acceptance. This script never closes tickets or the sprint and never dispatches workflows or changes production.

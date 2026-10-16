# Playground access disclosure (#88)

## Implementation and review boundary

The public venue projection now includes `access`. The safe mapper exposes that
field without internal notes/review history. Directory and Home use VenueCard;
surprise uses VenueSpotlight; detail uses the same VenueAccess component. The
notice precedes the maps action in DOM/reading order and is not truncated.

Public/yes, customer, resident, permit, permissive and unknown information have
distinct wording. Access does not imply free entry, opening hours, booking or
independently verified suitability. Unrecognised tags use the unknown notice.
Resident/permit records are not described as unrestricted public access.

No migration, source activation or production data/publication change is part of
this patch. Existing `public_visible` eligibility remains authoritative. A
read-only production check on 16 October found all 1,659 private and 41 no-access
playgrounds hidden. Both current nearby RPCs return the source access field;
the app explicitly maps public fields before sending results to browsers.

## Owner sample review, 16 October 2026

The twelve real samples and source links are retained in issue #88. Imran
confirmed the ten other samples and clarified:

- Little Garden (`4437eb40-96da-4548-935f-a0a22c9ad7ff`) is a nursery. Prepare a
  bounded classification correction from Children's playground to Nursery,
  with current-row fingerprint and before/after evidence before application.
  Nursery status does not establish visitor access. No row is changed here.
- Midland Terrace Gardens (`1ffbe6aa-7753-4fc7-b5f4-a47dd2685b94`) is a
  public-access playground. Preserve publication and the recorded owner evidence.
  The imported access field remains null: this patch does not silently rewrite
  source tags or expose internal review reasons as public claims.

## Verification and remaining gates

- Four new regression checks cover access semantics, safe mapping, actual rendered
  card/surprise notices before navigation and detail/shared component wiring.
- Existing public discovery and real PostgreSQL radius tests cover hidden rows,
  bounded reads, counts/paging and safe API projection.
- Public discovery CI includes the new tests.
- Preview presentation review must precede merge/release. Inspect customer and
  resident detail examples plus unknown/public wording; exercise directory/Home
  cards and surprise in the preview. Private/no example details must stay 404.
- No repeat factual scoring of the twelve examples is needed. Owner confirmation
  concerns presentation and any concrete bounded data correction.
- After approved release, verify current production paths before closing #88.
  Track Little Garden's unapplied correction explicitly; do not claim it fixed.

Rollback is reverting the application commit; no database rollback is needed.

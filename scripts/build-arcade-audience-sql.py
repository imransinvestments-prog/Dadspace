"""Build the arcade audience transaction from the 14 October 2026 publication review.

Owner rule, 22 October 2026: amusement arcades are listed only when confirmed family-
friendly. The 14 October review (artefacts/data/venue-publication-review-2026-10-14.json)
already screened all 601 arcades against the Gambling Commission premises register and
operator policies; this turns those decisions into the venues.adult_only flag:
  hide                 -> true   (adult gaming register match or operator 18+ policy)
  retain-family        -> false  (family entertainment or operator evidence)
  hide-pending-review  -> null   (casino-named quarantine, never asserted adult-only)
  retain-unverified    -> null   (no evidence either way)
and writes supabase/arcade-audience-2026-10-22.sql for the owner to run after the
20261022170000_venue_adult_only migration.

  python scripts/build-arcade-audience-sql.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "artefacts/data/venue-publication-review-2026-10-14.json"
OUTPUT = ROOT / "supabase/arcade-audience-2026-10-22.sql"
FLAG = {"hide": "true", "retain-family": "false", "hide-pending-review": "null", "retain-unverified": "null"}
RULE = ("2026-10-22 owner rule: amusement arcades are listed only when confirmed family-friendly "
        "(adult_only = false). No family evidence yet; not asserted to be adult-only.")
# A few adult-flagged arcades are still public (the 14 Oct hide matched exact names only);
# they are hidden with a reason that cites their adult evidence, not the no-evidence wording.
ADULT_RULE = ("2026-10-22 owner rule: amusement arcades are listed only when confirmed family-friendly. "
              "Adult evidence from the 2026-10-14 review (see adult_only_evidence).")


def sql_text(value):
    return "'" + str(value).replace("'", "''") + "'"


def build(decisions):
    unknown = sorted({d["decision"] for d in decisions} - FLAG.keys())
    if unknown:
        raise ValueError(f"unmapped review decisions: {unknown}")
    values = ",\n  ".join(f"({sql_text(d['source_url'])}, {FLAG[d['decision']]}::boolean, {sql_text('2026-10-14 review: ' + d['reason'])})"
                          for d in decisions)
    counts = {k: sum(d["decision"] == k for d in decisions) for k in FLAG}
    return f"""-- Arcade audience flag and owner publication rule, 22 October 2026.
-- Run after supabase/migrations/20261022170000_venue_adult_only.sql.
-- Flags come from the 14 October review of all {len(decisions)} arcades: {counts['hide']} adult (true),
-- {counts['retain-family']} family (false), {counts['hide-pending-review'] + counts['retain-unverified']} no evidence (null).
-- Then every public arcade not confirmed family-friendly is hidden. Records are not deleted.
-- Reviewed records keep their decisions (venues_preserve_operations_review).
begin;
with evidence(source_url, adult_only, reason) as (values
  {values}
)
update public.venues v set adult_only = e.adult_only, adult_only_evidence = e.reason
from evidence e
where v.source_url = e.source_url and v.category = 'Amusement arcade';

update public.venues
set public_visible = false, review_reason = concat_ws(' ', review_reason, {sql_text(ADULT_RULE)})
where category = 'Amusement arcade' and public_visible and adult_only;

update public.venues
set public_visible = false, review_reason = concat_ws(' ', review_reason, {sql_text(RULE)})
where category = 'Amusement arcade' and public_visible and adult_only is null;

-- Expect: public arcades = family-flagged public arcades (about {counts['retain-family']}); no public adult arcades.
select count(*) filter (where public_visible) as public_arcades,
       count(*) filter (where public_visible and adult_only = false) as public_family_arcades,
       count(*) filter (where public_visible and adult_only) as public_adult_arcades,
       count(*) filter (where adult_only) as adult_flagged,
       count(*) filter (where adult_only is null) as no_evidence
from public.venues where category = 'Amusement arcade';
commit;

-- Rollback of the publication rule only (the flag itself is harmless to keep). If the
-- 20261022190000 arcade publication guard is installed, pause it for this statement:
-- alter table public.venues disable trigger venues_arcade_publication_guard;
-- update public.venues set public_visible = true,
--   review_reason = nullif(trim(replace(replace(review_reason, {sql_text(RULE)}, ''), {sql_text(ADULT_RULE)}, '')), '')
-- where category = 'Amusement arcade' and review_reason like '%2026-10-22 owner rule: amusement arcades%';
-- alter table public.venues enable trigger venues_arcade_publication_guard;
"""


def main():
    decisions = json.loads(REVIEW.read_text(encoding="utf-8"))["decisions"]
    OUTPUT.write_text(build(decisions), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} for {len(decisions)} arcades")
    return 0


if __name__ == "__main__":
    sys.exit(main())

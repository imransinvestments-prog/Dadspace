-- Owner-authorized follow-up, 14 October 2026. Publication change only.
-- Parks/playgrounds with explicit access=no OR missing/blank access are hidden.
-- Unknown access is not evidence of restricted access: hold pending review.
-- Save prior visibility/review fields before running; do not blindly republish
-- records with subsequent reviews when restoring the snapshot.
begin;
update public.venues
set public_visible=false,
    review_reason=concat_ws(E'\n', nullif(review_reason,''),
      case when lower(trim(access))='no'
        then '2026-10-14 owner decision: hide park/playground with imported access=no. Evidence: ' || coalesce(source_url,'source unavailable')
        else '2026-10-14 owner decision: hide park/playground pending access evidence because access is missing. This does not confirm private or restricted access. Source: ' || coalesce(source_url,'source unavailable')
      end),
    ops_reviewed_at=now()
where public_visible=true
  and (category ilike '%playground%' or category ilike '%park%')
  and (access is null or trim(access)='' or lower(trim(access))='no');
commit;

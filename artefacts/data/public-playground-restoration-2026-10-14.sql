-- HISTORICAL AUDIT ONLY: exact owner-authorized restoration transaction.
-- Do not schedule or replay as a migration or general publishing policy.
-- Owner confirmed playgrounds with missing access information are public.
begin;
-- Intentional owner review update; preserve the normal importer safeguard.
set local dadspace.review_write='on';
update public.venues set public_visible=true, review_reason=concat_ws(E'\n',nullif(review_reason,''),'2026-10-14 owner confirmation: playground is accessible to the public. Restore publication; this supersedes the earlier hold for missing access information. Imported access value and source evidence retained.'), ops_reviewed_at=now() where category ilike '%playground%' and (access is null or trim(access)='') and public_visible=false;
commit;


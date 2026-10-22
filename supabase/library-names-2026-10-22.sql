-- Owner rule, 22 October 2026 (#92): a public library whose name is only a place gets "Library"
-- added ("Fulham" -> "Fulham Library"). Only plain place names change: 1,253 rows on 22 Oct.
-- Left unchanged for owner review: names that already say Library (193), names with a building or
-- service word such as archives, record office, community hub, mobile, book drop or café, or with
-- brackets or "&" (192), and prison/YOI libraries (35), which also need a visibility decision.
-- The reference importer never overwrites an existing name and every row keeps its source record,
-- so a re-import cannot revert or duplicate these. The source name is kept in the note.
begin;
-- None of these rows is review-locked today; this keeps the rename applying if one becomes so.
set local dadspace.review_write = 'on';

create temp table library_renames on commit drop as
select id, btrim(venue_name) as old_name from public.venues
where category = 'library' and public_visible and btrim(venue_name) !~* 'librar'
  and btrim(venue_name) !~* '\m(hmp|prison|yoi)\M'
  and btrim(venue_name) !~* '\m(centre|center|hub|store|service|services|archives?|point|house|room|institute|mobile|link|shop|café|cafe|office|drop|studies)\M'
  and btrim(venue_name) !~ '[()&/,]';

do $$
declare n int := (select count(*) from library_renames);
begin
  if n <> 1253 then
    raise exception 'Expected 1253 libraries to rename, found %. The data changed after 22 Oct; re-check before running.', n;
  end if;
end $$;

update public.venues v set
  venue_name = r.old_name || ' Library',
  notes = concat_ws(' ', nullif(btrim(v.notes), ''), 'Display name: "Library" added 2026-10-22 at owner request (#92); source name "' || r.old_name || '".')
from library_renames r where v.id = r.id;

-- Expect 1253.
select count(*) as renamed from public.venues where notes like '%"Library" added 2026-10-22%';
commit;

-- Rollback: remove the added " Library" and the note, for rows this file changed.
-- update public.venues set
--   venue_name = left(venue_name, length(venue_name) - length(' Library')),
--   notes = nullif(btrim(regexp_replace(notes, '\s*Display name: "Library" added 2026-10-22 at owner request \(#92\); source name "[^"]*"\.', '')), '')
-- where notes like '%"Library" added 2026-10-22%' and venue_name like '% Library';

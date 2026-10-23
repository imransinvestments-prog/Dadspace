-- OpenActive feed sources (activities PR 2). Owner-run; inserts INACTIVE rows only.
-- Both datasets publish under CC BY 4.0 (survey: artefacts/data/openactive-survey-2026-10-23.json).
-- The adapter refuses any other licence at run time and credits the publisher on every listing.
-- Activate a row only after the owner approves it: update public.sources set active = true where url = '...';
-- Rollback: delete from public.sources where source_adapter = 'openactive_feed' and last_checked_at is null;

insert into public.sources
  (name, url, category, kind, org_type, focus, nation, region, fetch_method,
   active, notes, source_role, source_adapter)
values
  ('Places Leisure (OpenActive)',
   'https://placesleisure.gs-signature.cloud/OpenActive/',
   'activities', 'operator', 'leisure_operator',
   'leisure-centre sessions for ages 0–5', 'England', null, 'requests',
   false,
   'OpenActive SessionSeries/CourseInstance feeds, CC BY 4.0. Read-only check 23 Oct 2026: 20,489 series, 816 with an ageRange overlapping 0–5 and a weekly schedule, grouped into 68 activities (7 within 10 km of W3 9LN). Zero model calls. Inactive until owner approval.',
   'activity_listing', 'openactive_feed'),
  ('Everyone Active (OpenActive)',
   'https://data.everyoneactive.com/OpenActive/',
   'activities', 'operator', 'leisure_operator',
   'leisure-centre sessions for ages 0–5', 'England', null, 'requests',
   false,
   'OpenActive SessionSeries/CourseInstance feeds, CC BY 4.0. Survey 23 Oct 2026: 99,244 series, 3,011 age-eligible, 70 pilot-local. Zero model calls. Inactive until owner approval.',
   'activity_listing', 'openactive_feed')
on conflict (url) do nothing;

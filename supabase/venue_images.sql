-- Applied with the Supabase migration tool as add_licensed_venue_images.
-- Existing RLS, visibility rules and venue records are unchanged.
alter table public.venues
  add column if not exists image_url text,
  add column if not exists image_source_url text,
  add column if not exists image_attribution text,
  add column if not exists image_license text,
  add column if not exists image_license_url text,
  add column if not exists image_title text,
  add column if not exists image_credit text,
  add column if not exists image_match_method text,
  add column if not exists image_updated_at timestamptz;

comment on column public.venues.image_url is 'Optional source-linked venue photo. Missing or unusable photos use a labelled category illustration in the app.';
comment on column public.venues.image_source_url is 'Original file page with photographer and licence information; displayed with the image.';

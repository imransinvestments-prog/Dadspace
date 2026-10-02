-- Stable event identity for Dadspace events/activities.
-- identity_key answers "which real-world listing is this?" while content_hash
-- answers "did the extracted content change?". Existing dedupe_key is retained
-- for backward compatibility but is no longer the upsert conflict target.

alter table public.collected_events
  add column if not exists identity_key text,
  add column if not exists content_hash text;

create unique index if not exists collected_events_identity_key_unique
  on public.collected_events (identity_key)
  where identity_key is not null;

comment on column public.collected_events.identity_key is
  'Stable listing identity. Prefer specific event URL + date + venue; fall back to normalized title + date + venue.';
comment on column public.collected_events.content_hash is
  'Hash of mutable extracted/display fields, separate from stable identity.';

create table public.original_posts (
 slug text primary key check (slug ~ '^[a-z0-9-]+$'),
 cadence text not null check (cadence in ('daily','weekly')),
 slot_date date not null,
 title text not null check (length(title) between 10 and 120),
 summary text not null check (length(summary) between 40 and 320),
 sections jsonb not null check (jsonb_typeof(sections) = 'array'),
 topic text not null,
 model text not null,
 published_at timestamptz not null default now(),
 unique(cadence,slot_date)
);
create index original_posts_published_idx on public.original_posts(published_at desc);
alter table public.original_posts enable row level security;
revoke all on public.original_posts from anon, authenticated;
grant select on public.original_posts to anon, authenticated;
grant all on public.original_posts to service_role;
create policy original_posts_public_read on public.original_posts for select to anon, authenticated using (published_at <= now());

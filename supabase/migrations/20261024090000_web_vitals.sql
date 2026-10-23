-- Field Core Web Vitals recorded by the site itself (#141; app/api/vitals/route.ts).
-- Vercel Hobby hides per-metric Speed Insights. Rows carry no IP address, user agent,
-- query string or account: only the metric, page path and a coarse device class.
-- Service role only. Rollback: drop table public.web_vitals;
create table if not exists public.web_vitals (
  id bigint generated always as identity primary key,
  recorded_at timestamptz not null default now(),
  metric text not null check (metric in ('LCP', 'INP', 'CLS', 'FCP', 'TTFB')),
  value double precision not null check (value >= 0 and value <= 600000),
  rating text check (rating in ('good', 'needs-improvement', 'poor')),
  metric_id text not null unique check (char_length(metric_id) <= 100),
  navigation_type text check (char_length(navigation_type) <= 30),
  route text not null check (char_length(route) <= 200 and left(route, 1) = '/'),
  device text not null check (device in ('mobile', 'desktop'))
);

create index if not exists web_vitals_metric_time_idx
  on public.web_vitals (metric, device, recorded_at desc);

alter table public.web_vitals enable row level security;
revoke all on public.web_vitals from public, anon, authenticated, service_role;
grant select, insert on public.web_vitals to service_role;
create policy web_vitals_service_read on public.web_vitals
  for select to service_role using (true);
create policy web_vitals_service_insert on public.web_vitals
  for insert to service_role with check (true);

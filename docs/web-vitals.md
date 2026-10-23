# Field Core Web Vitals

Vercel Speed Insights on the Hobby plan shows only the combined Real Experience Score; the per-metric LCP, INP and CLS figures need a paid plan. #141's field criteria need those metrics (p75 LCP ≤2.5s, INP ≤200ms, CLS ≤0.1), so the site records its own.

## How it works

- `components/web-vitals-reporter.tsx` uses Next's `useReportWebVitals` and sends each LCP, INP, CLS, FCP and TTFB report with `navigator.sendBeacon` to `/api/vitals`.
- `app/api/vitals/route.ts` stores **production** reports only, in `public.web_vitals` (migration `20261024090000_web_vitals.sql`). Preview and local traffic is ignored.
- `lib/web-vitals.ts` validates each report and drops crawlers, Lighthouse/PageSpeed and headless browsers, so lab runs do not mix into field data.
- A row holds the metric, value, rating, the web-vitals report id (used to ignore resent beacons), navigation type, page **path** (never the query string) and `mobile`/`desktop` from the user agent. No IP address, user agent, account or location is stored.
- LCP, FCP, TTFB and INP are milliseconds; CLS is unitless.

## Setup

Apply the migration once (SQL editor, or `supabase db push`). Until the table exists, beacons are accepted and silently not stored.

## p75 report

Detail pages are grouped (e.g. `/events/[detail]`). Change the interval as needed.

```sql
select metric, device,
       case when route ~ '^/[^/]+/.+' then '/' || split_part(route, '/', 2) || '/[detail]' else route end as page,
       count(*) as samples,
       round(percentile_cont(0.75) within group (order by value)::numeric, 3) as p75,
       round(100.0 * avg((rating = 'good')::int), 1) as pct_good
from public.web_vitals
where recorded_at > now() - interval '7 days'
group by 1, 2, 3
having count(*) >= 20
order by page, device, metric;
```

To check for the lab bimodality on mobile Home (about 3–4s vs about 9s LCP):

```sql
select width_bucket(value, 0, 12000, 12) * 1000 as lcp_ms_bucket_upper, count(*)
from public.web_vitals
where metric = 'LCP' and device = 'mobile' and route = '/' and recorded_at > now() - interval '7 days'
group by 1 order by 1;
```

Treat fewer than about 50 samples per page and device as indicative only.

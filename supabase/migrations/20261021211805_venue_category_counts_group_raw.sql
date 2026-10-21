-- venue_category_counts normalised the category of every visible venue (~56k
-- regexp_replace calls, ~2.4s) on each homepage and /venues load. Normalising is
-- a function of the raw category alone, so count per raw category first and
-- normalise only the handful of distinct values. Same signature and rows, so the
-- deployed app keeps working unchanged.
create or replace function public.venue_category_counts()
returns table(key text,count bigint) language sql stable security invoker set search_path = public
as $$
  select regexp_replace(lower(category),'[[:space:]&-]+','_','g'), sum(n)::bigint
  from (select category, count(*) n from public.venues where public_visible=true and category is not null group by category) raw
  group by 1 order by 2 desc
$$;
revoke all on function public.venue_category_counts() from public,anon,authenticated;
grant execute on function public.venue_category_counts() to service_role;

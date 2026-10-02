-- Apply via Supabase apply_migration. Sort the complete public directory before paging.
create or replace function public.nearby_venue_page(
  p_lat double precision default null, p_lng double precision default null,
  p_query text default '', p_category text default 'all',
  p_free boolean default false, p_indoor boolean default false, p_outdoor boolean default false,
  p_offset integer default 0, p_limit integer default 24
) returns jsonb language sql stable security invoker set search_path = public
as $$
  with filtered as materialized (
    select v.*, case when p_lat between -90 and 90 and p_lng between -180 and 180
      and v.latitude between -90 and 90 and v.longitude between -180 and 180
      then 7917.6 * asin(sqrt(least(1.0, greatest(0.0,
        power(sin(radians(v.latitude-p_lat)/2),2) + cos(radians(p_lat))*cos(radians(v.latitude))*power(sin(radians(v.longitude-p_lng)/2),2)
      )))) else null end as distance_miles
    from public.venues v
    where v.public_visible = true
      and (p_category = 'all' or regexp_replace(lower(v.category), '[[:space:]&-]+', '_', 'g') = p_category)
      and (not p_free or lower(v.fee) in ('no','free'))
      and (not p_indoor or to_jsonb(v)->>'indoor' = 'true')
      and (not p_outdoor or to_jsonb(v)->>'outdoor' = 'true')
      and (coalesce(p_query,'') = '' or strpos(lower(concat_ws(' ',v.venue_name,v.venue_label,v.town_city,v.postcode,v.address)),lower(left(p_query,100))) > 0)
  ), page as (
    select * from filtered order by distance_miles nulls last, coalesce(nullif(venue_name,''),venue_label), id
    offset greatest(0,p_offset) limit least(48,greatest(1,p_limit))
  )
  select jsonb_build_object('rows',coalesce((select jsonb_agg(to_jsonb(p) order by p.distance_miles nulls last, coalesce(nullif(p.venue_name,''),p.venue_label), p.id) from page p),'[]'::jsonb),
    'total',(select count(*) from filtered));
$$;
revoke all on function public.nearby_venue_page(double precision,double precision,text,text,boolean,boolean,boolean,integer,integer) from public,anon,authenticated;
grant execute on function public.nearby_venue_page(double precision,double precision,text,text,boolean,boolean,boolean,integer,integer) to service_role;

create or replace function public.venue_category_counts()
returns table(key text,count bigint) language sql stable security invoker set search_path = public
as $$ select regexp_replace(lower(category),'[[:space:]&-]+','_','g'),count(*) from public.venues where public_visible=true and category is not null group by 1 order by 2 desc $$;
revoke all on function public.venue_category_counts() from public,anon,authenticated;
grant execute on function public.venue_category_counts() to service_role;

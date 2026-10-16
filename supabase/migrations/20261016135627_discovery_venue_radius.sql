-- Add a new signature so the currently deployed app keeps its existing RPC.
-- Only the new directory route calls this function; no venue rows are changed.
create or replace function public.discovery_venue_page(
  p_lat double precision default null, p_lng double precision default null,
  p_query text default '', p_category text default 'all', p_free boolean default false,
  p_offset integer default 0, p_limit integer default 24,
  p_radius_km double precision default 10, p_scope text default 'local'
) returns jsonb language plpgsql stable security invoker set search_path = public
as $$
begin
  if p_radius_km is null or not (p_radius_km > 0 and p_radius_km <= 100)
    or p_scope is null or p_scope not in ('local', 'unknown') then
    raise exception 'Invalid radius or scope' using errcode = '22023';
  end if;
  if (p_lat is null) <> (p_lng is null)
    or (p_lat is not null and not (p_lat between -90 and 90 and p_lng between -180 and 180))
    or (p_lat is null and p_scope <> 'local') then
    raise exception 'Invalid location' using errcode = '22023';
  end if;
  return (
    with candidates as materialized (
      -- Keep the working set narrow; joining full records before sorting spills
      -- descriptions and image metadata to disk across the national inventory.
      select v.id, coalesce(nullif(btrim(v.venue_name),''),nullif(btrim(v.venue_label),'')) as sort_name,
        case when p_lat is not null
          and v.latitude between -90 and 90 and v.longitude between -180 and 180
        then 12742 * asin(sqrt(least(1.0, greatest(0.0,
          power(sin(radians(v.latitude-p_lat)/2),2)
          + cos(radians(p_lat))*cos(radians(v.latitude))*power(sin(radians(v.longitude-p_lng)/2),2)
        )))) else null end as distance_km
      from public.venues v
      where v.public_visible = true
        and coalesce(nullif(btrim(v.venue_name),''),nullif(btrim(v.venue_label),'')) is not null
        and (p_category = 'all' or regexp_replace(lower(v.category), '[[:space:]&-]+', '_', 'g') = p_category)
        and (not p_free or lower(v.fee) in ('no','free'))
        and (coalesce(p_query,'') = '' or strpos(lower(concat_ws(' ',v.venue_name,v.venue_label,v.town_city,v.postcode,v.address)),lower(left(p_query,100))) > 0)
    ), eligible as materialized (
      select * from candidates
      where p_lat is null
        or (p_scope = 'local' and distance_km <= p_radius_km)
        or (p_scope = 'unknown' and distance_km is null)
    ), page as (
      select * from eligible order by distance_km nulls last, sort_name, id
      offset greatest(0,p_offset) limit least(48,greatest(1,p_limit))
    )
    select jsonb_build_object(
      'rows',coalesce((select jsonb_agg(
        to_jsonb(v) || jsonb_build_object('distance_miles',p.distance_km / 1.609344)
        order by p.distance_km nulls last,p.sort_name,p.id)
        from page p join public.venues v on v.id=p.id),'[]'::jsonb),
      'total',(select count(*) from eligible))
  );
end;
$$;
revoke all on function public.discovery_venue_page(double precision,double precision,text,text,boolean,integer,integer,double precision,text) from public,anon,authenticated;
grant execute on function public.discovery_venue_page(double precision,double precision,text,text,boolean,integer,integer,double precision,text) to service_role;

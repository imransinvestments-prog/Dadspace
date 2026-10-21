-- Homepage local places: the nearest few venues per category without scanning
-- the national inventory. nearby_venue_page computed a distance for every
-- visible venue on each of ~10 per-category calls per homepage view; it is left
-- unchanged so the currently deployed app keeps its existing RPC.
--
-- A rough box is widened until the nearest p_limit venues are provably inside
-- it: every venue outside the circle of radius r is farther than every venue
-- within it, so results match an unbounded nearest-first read exactly. Boxes
-- that would cross the antimeridian or a pole are skipped, and too few matches
-- fall back to the national read. Venues without coordinates are never returned,
-- matching the homepage route, which discards them.
create index if not exists venues_public_lat_lng_idx
  on public.venues (latitude, longitude)
  where public_visible;

-- Rare categories (2-3 venues nationally) always reach the national read; this
-- keeps that read to the category's own rows.
create index if not exists venues_public_category_key_idx
  on public.venues (regexp_replace(lower(category), '[[:space:]&-]+', '_', 'g'))
  where public_visible;

create or replace function public.nearby_venue_rows(
  p_lat double precision, p_lng double precision,
  p_category text default 'all', p_limit integer default 6
) returns jsonb language plpgsql stable security invoker
set search_path = public
-- p_category = 'all' must fold away per call so the category index stays usable.
set plan_cache_mode = force_custom_plan
as $$
declare
  v_limit integer := least(48, greatest(1, coalesce(p_limit, 6)));
  v_radius double precision;
  v_reach double precision;
  v_dlat double precision;
  v_dlng double precision;
  v_ids uuid[];
begin
  if p_lat is null or p_lng is null or not (p_lat between -90 and 90 and p_lng between -180 and 180) then
    raise exception 'Invalid location' using errcode = '22023';
  end if;
  foreach v_radius in array array[10, 40, 160, 640]::double precision[] loop
    -- Spherical extents of the circle, padded so rounding never trims its edge.
    v_reach := v_radius * 1.001 / 6371;
    continue when cos(radians(p_lat)) <= sin(v_reach);
    v_dlat := degrees(v_reach);
    v_dlng := degrees(asin(sin(v_reach) / cos(radians(p_lat))));
    continue when p_lat - v_dlat < -90 or p_lat + v_dlat > 90 or p_lng - v_dlng < -180 or p_lng + v_dlng > 180;
    select array_agg(n.id order by n.distance_km, n.sort_name, n.id) into v_ids from (
      select c.id, c.sort_name, c.distance_km from (
        select v.id, coalesce(nullif(v.venue_name,''), v.venue_label) as sort_name,
          12742 * asin(sqrt(least(1.0, greatest(0.0,
            power(sin(radians(v.latitude-p_lat)/2),2) + cos(radians(p_lat))*cos(radians(v.latitude))*power(sin(radians(v.longitude-p_lng)/2),2)
          )))) as distance_km
        from public.venues v
        where v.public_visible
          and v.latitude between p_lat - v_dlat and p_lat + v_dlat
          and v.longitude between p_lng - v_dlng and p_lng + v_dlng
          and (p_category = 'all' or regexp_replace(lower(v.category), '[[:space:]&-]+', '_', 'g') = p_category)
      ) c
      where c.distance_km <= v_radius
      order by c.distance_km, c.sort_name, c.id
      limit v_limit
    ) n;
    exit when coalesce(cardinality(v_ids), 0) = v_limit;
    v_ids := null;
  end loop;
  if v_ids is null then
    select array_agg(n.id order by n.distance_km, n.sort_name, n.id) into v_ids from (
      select v.id, coalesce(nullif(v.venue_name,''), v.venue_label) as sort_name,
        12742 * asin(sqrt(least(1.0, greatest(0.0,
          power(sin(radians(v.latitude-p_lat)/2),2) + cos(radians(p_lat))*cos(radians(v.latitude))*power(sin(radians(v.longitude-p_lng)/2),2)
        )))) as distance_km
      from public.venues v
      where v.public_visible
        and v.latitude between -90 and 90 and v.longitude between -180 and 180
        and (p_category = 'all' or regexp_replace(lower(v.category), '[[:space:]&-]+', '_', 'g') = p_category)
      order by distance_km, sort_name, id
      limit v_limit
    ) n;
  end if;
  return jsonb_build_object('rows', coalesce((select jsonb_agg(
      to_jsonb(v) || jsonb_build_object('distance_miles', 7917.6 * asin(sqrt(least(1.0, greatest(0.0,
        power(sin(radians(v.latitude-p_lat)/2),2) + cos(radians(p_lat))*cos(radians(v.latitude))*power(sin(radians(v.longitude-p_lng)/2),2))))))
      order by array_position(v_ids, v.id))
    from public.venues v where v.id = any(v_ids)), '[]'::jsonb));
end;
$$;
revoke all on function public.nearby_venue_rows(double precision,double precision,text,integer) from public,anon,authenticated;
grant execute on function public.nearby_venue_rows(double precision,double precision,text,integer) to service_role;

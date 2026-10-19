-- Additive reference capability only. No data import, public access or app cutover.
create table public.geography_releases (
  id text primary key check(length(id) between 3 and 100),
  content_sha256 text not null check(content_sha256 ~ '^[0-9a-f]{64}$'),
  edition text not null,
  source_url text not null check(source_url like 'https://%'),
  licence text not null,
  scope text not null,
  provenance jsonb not null check(jsonb_typeof(provenance)='object'),
  observed_at timestamptz not null,
  imported_at timestamptz not null default now(),
  import_transaction bigint not null default txid_current()
);
create table public.geography_areas (
  release_id text not null references public.geography_releases(id),
  code text not null,
  name text not null check(length(trim(name)) > 0),
  kind text not null check(kind in ('nation','region','county','council','postal_area','postal_district','postal_sector')),
  primary key(release_id,code)
);
create table public.geography_relationships (
  release_id text not null,
  child_code text not null,
  parent_code text not null,
  kind text not null check(kind in ('administrative','postal')),
  primary key(release_id,child_code,parent_code),
  unique(release_id,child_code),
  foreign key(release_id,child_code) references public.geography_areas(release_id,code),
  foreign key(release_id,parent_code) references public.geography_areas(release_id,code),
  check(child_code <> parent_code)
);
create table public.geography_postcodes (
  release_id text not null,
  postcode text not null check(postcode ~ '^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$' and postcode not like 'BT%'),
  sector_code text not null,
  council_code text not null,
  nation_code text not null,
  latitude double precision not null check(latitude between 49 and 61.5),
  longitude double precision not null check(longitude between -9 and 2.5),
  introduced date,
  terminated date,
  coordinate_method text not null,
  primary key(release_id,postcode),
  foreign key(release_id,sector_code) references public.geography_areas(release_id,code),
  foreign key(release_id,council_code) references public.geography_areas(release_id,code),
  foreign key(release_id,nation_code) references public.geography_areas(release_id,code),
  check(terminated is null or introduced is null or terminated >= introduced)
  ,check(sector_code='P:'||left(postcode,length(postcode)-2))
);
create index geography_postcodes_council_idx on public.geography_postcodes(release_id,council_code);

create function public.geography_validate_reference() returns trigger
language plpgsql set search_path=public,pg_temp as $$
declare child_kind text; parent_kind text; nation text;
begin
  if tg_op <> 'INSERT' then raise exception 'Reference releases are immutable; import a new release'; end if;
  if not exists(select 1 from geography_releases where id=new.release_id and import_transaction=txid_current())
  then raise exception 'Import all reference rows in the release creation transaction'; end if;
  if tg_table_name='geography_relationships' then
    select kind into child_kind from geography_areas where release_id=new.release_id and code=new.child_code;
    select kind into parent_kind from geography_areas where release_id=new.release_id and code=new.parent_code;
    if not coalesce((new.kind='administrative' and (
      (child_kind='region' and parent_kind='nation') or
      (child_kind='county' and parent_kind in ('nation','region')) or
      (child_kind='council' and parent_kind in ('nation','region','county')))) or
      (new.kind='postal' and ((child_kind='postal_sector' and parent_kind='postal_district') or
                             (child_kind='postal_district' and parent_kind='postal_area'))),false)
    then raise exception 'Invalid geography relationship'; end if;
  elsif tg_table_name='geography_postcodes' then
    if not exists(select 1 from geography_areas where release_id=new.release_id and code=new.sector_code and kind='postal_sector') or
       not exists(select 1 from geography_areas where release_id=new.release_id and code=new.council_code and kind='council') or
       not exists(select 1 from geography_areas where release_id=new.release_id and code=new.nation_code and kind='nation')
    then raise exception 'Invalid postcode area mapping'; end if;
    with recursive ancestors(code) as (
      select new.council_code union
      select r.parent_code from geography_relationships r join ancestors a on r.child_code=a.code where r.release_id=new.release_id
    ) select a.code into nation from ancestors a join geography_areas g on g.release_id=new.release_id and g.code=a.code and g.kind='nation';
    if nation is distinct from new.nation_code then raise exception 'Postcode nation disagrees with council'; end if;
  end if;
  return new;
end $$;
create trigger geography_relationship_guard before insert or update or delete on public.geography_relationships for each row execute function public.geography_validate_reference();
create trigger geography_postcode_guard before insert or update or delete on public.geography_postcodes for each row execute function public.geography_validate_reference();
create trigger geography_area_immutable before insert or update or delete on public.geography_areas for each row execute function public.geography_validate_reference();
create trigger geography_release_immutable before update or delete on public.geography_releases for each row execute function public.geography_validate_reference();
revoke all on function public.geography_validate_reference() from public,anon,authenticated;

alter table public.geography_releases enable row level security;
alter table public.geography_areas enable row level security;
alter table public.geography_relationships enable row level security;
alter table public.geography_postcodes enable row level security;
revoke all on public.geography_releases, public.geography_areas, public.geography_relationships, public.geography_postcodes from public,anon,authenticated,service_role;
grant select on public.geography_releases, public.geography_areas, public.geography_relationships, public.geography_postcodes to service_role;
create policy geography_release_service_read on public.geography_releases for select to service_role using(true);
create policy geography_area_service_read on public.geography_areas for select to service_role using(true);
create policy geography_relationship_service_read on public.geography_relationships for select to service_role using(true);
create policy geography_postcode_service_read on public.geography_postcodes for select to service_role using(true);

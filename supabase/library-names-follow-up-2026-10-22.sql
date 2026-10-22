-- Owner decisions, 22 October 2026 (#92), following supabase/library-names-2026-10-22.sql:
-- 1. Mobile libraries are named "<name> Mobile Library" (35); nameless ones take their county.
-- 2. Place names with brackets or "&" get "Library" after the place (7).
-- 3. Three obvious typos are corrected (Rochester, Wallsend, Nottinghamshire).
-- 4. Prison and YOI libraries are hidden from public listings because they are not open to the
--    public (35). Records are kept, not deleted, and stay out of the operations review queue.
-- Community hubs, book drops, reading cafés and archives keep their names. Every row is pinned by
-- id and its current name; the run stops if any row has changed since 22 Oct.
begin;
-- No library row is review-locked today; this keeps the change applying if one becomes so.
set local dadspace.review_write = 'on';

create temp table library_names(id uuid primary key, old_name text not null, new_name text not null) on commit drop;
insert into library_names values
  ('5237cfed-b252-48ed-bde3-4b225c3a27b3', 'Brooks Mobile', 'Brooks Mobile Library'),
  ('f7c9a04f-f6d5-4f3f-9f3f-1ef700bb756e', 'Children''s Mobile North', 'Children''s Mobile Library North'),
  ('35c94193-45b1-4819-9539-4331d6611224', 'Children''s Mobile Sorth', 'Children''s Mobile Library South'),
  ('4711c07c-54de-4ec6-a01e-4396126d7512', 'Community Mobile', 'Community Mobile Library'),
  ('f08ae5cc-330e-40b9-8215-be28ac25db88', 'County Mobile 1', 'County Mobile Library 1'),
  ('92f3d85b-b563-471c-bf7a-e7d4ebd812e6', 'County Mobile 2', 'County Mobile Library 2'),
  ('738b4fc9-771e-4f95-b638-9e28d399b9af', 'East Mobile', 'East Mobile Library'),
  ('9d96e8e0-d07b-4899-a1f2-e0794528b84c', 'East-South Mobile', 'East-South Mobile Library'),
  ('d4cc0519-fc65-4878-975b-dbde70661713', 'Exmouth Mobile', 'Exmouth Mobile Library'),
  ('f22a8f2d-d6fd-4933-947a-b74d52b7d33d', 'Ivybridge Mobile', 'Ivybridge Mobile Library'),
  ('0db8b29c-7eeb-4e2d-be20-4a971a2232c3', 'Kenilworth Mobile L ibrary', 'Kenilworth Mobile Library'),
  ('0550cd63-96ff-485f-8a6b-8a27a64e99fb', 'mobile', 'Northumberland Mobile Library'),
  ('af5d6291-b760-4fe1-b62d-30b7e4be3a84', 'mobile', 'Northumberland Mobile Library'),
  ('9040ab68-b532-49f7-aad1-5aa8d777519d', 'mobile', 'Northumberland Mobile Library'),
  ('59702e81-21fe-4a16-820a-f44d71cbba07', 'Mobile', 'Peterborough Mobile Library'),
  ('c4c07d8d-6564-465d-9e8e-485753529610', 'Mobile 1', 'Staffordshire Mobile Library 1'),
  ('1250446e-96a8-44b9-98cc-feb8b48ee325', 'Mobile A', 'Leicestershire Mobile Library A'),
  ('4fc79c30-19a2-4b94-890c-b1d79f835226', 'Mobile B', 'Leicestershire Mobile Library B'),
  ('4da64131-be36-48d1-9063-b414a9e3efc6', 'Mobile C', 'Leicestershire Mobile Library C'),
  ('839bb668-1b88-4088-bccb-8536a5e212d5', 'Mobile Ashford', 'Ashford Mobile Library'),
  ('95326951-2a50-4d55-8664-0fab10a55afc', 'Mobile Dover', 'Dover Mobile Library'),
  ('fc90bd78-8b2d-4bea-b02e-a570fad415ab', 'Mobile Maidstone', 'Maidstone Mobile Library'),
  ('0fa4e172-d0a0-4ee8-972e-7ec57d37518e', 'Mobile Northfleet', 'Northfleet Mobile Library'),
  ('4e42343b-3176-49ba-ab94-8cf5322040ea', 'Mobile Sturry', 'Sturry Mobile Library'),
  ('c925d61f-304c-48c0-b979-1a4ec8fb853c', 'North Mobile', 'North Mobile Library'),
  ('f85bc022-98c1-4659-9e44-10a853496b3d', 'North Mobile', 'North Mobile Library'),
  ('2b3e39d8-05ab-4d12-9d3f-307ebe0a5304', 'Owen Mobile', 'Owen Mobile Library'),
  ('9722ed32-e5b1-4280-8c81-7db2041d3c52', 'Sabrina Mobile', 'Sabrina Mobile Library'),
  ('b4bc3c96-e062-4409-ab71-f3869a2ffba1', 'Somerset Mobile', 'Somerset Mobile Library'),
  ('964638db-da4c-4842-b0f9-60eb0f0d4d4b', 'South Mobile', 'South Mobile Library'),
  ('6daed610-b834-473d-9235-ea0312ba011a', 'South Mobile', 'South Mobile Library'),
  ('cf9e62d6-3302-4ba2-8c91-3e4d6d11948d', 'Tiverton Mobile', 'Tiverton Mobile Library'),
  ('838727bf-63df-4f5e-afab-124fad6291ab', 'Torrington Mobile', 'Torrington Mobile Library'),
  ('76a3a77a-98a8-4114-9e01-dd25bd08b855', 'West Mobile', 'West Mobile Library'),
  ('b5d6579a-4455-4d3d-bd5b-5f556c0dacde', 'West Mobile', 'West Mobile Library'),
  ('8314e6f9-81d8-4cf7-976e-a121b01eb18f', 'Adswood & Bridgehall', 'Adswood & Bridgehall Library'),
  ('b723c40f-c100-4a0c-941b-a1cc32fc899d', 'Meadows (Maghull)', 'Meadows Library (Maghull)'),
  ('479d5f7c-5bbb-495f-b9a5-2d44e5c35588', 'Skegby & Stanton Hill', 'Skegby & Stanton Hill Library'),
  ('8337e6bf-2c34-4317-8012-6dcd0f1611fa', 'Springwood (In the Springwood Sports Centre)', 'Springwood Library (In the Springwood Sports Centre)'),
  ('8311467b-9cbf-49c3-9949-c5a8402e597d', 'Wakefield (Balne Lane)', 'Wakefield Library (Balne Lane)'),
  ('b30cb411-faef-407e-8bc0-86ed5e10396b', 'Wakefield (Drury Lane)', 'Wakefield Library (Drury Lane)'),
  ('26619005-e7b8-4ae5-9388-3f352dff8d5d', 'Walton (Life Rooms)', 'Walton Library (Life Rooms)'),
  ('cdfc806a-b507-4752-b0cf-2e03183b40e3', 'Rohester Community Hub', 'Rochester Community Hub'),
  ('584846ef-c9c8-4c21-9507-0f161311fa75', 'Walsend Customer First Centre', 'Wallsend Customer First Centre'),
  ('f562395d-0707-4441-8ba5-921f7165a5dc', 'Nottinghhamshire Archives', 'Nottinghamshire Archives');

create temp table prison_libraries(id uuid primary key) on commit drop;
insert into prison_libraries values
  ('10149519-c1cf-4587-b5c8-c9c98e887dc6'), ('aa436277-aed9-4200-9f2a-df3dbede6145'), ('ee13b989-7824-4397-aa91-68d350a8773f'),
  ('7a9b5147-35fa-4460-ad56-85aaee2825f7'), ('db6cac07-6f1c-4129-8c51-bb9294fa3e59'), ('b32fa65d-33f4-411f-912a-2eea2ab36195'),
  ('119dbdfa-6fce-4c05-b4aa-00663d976096'), ('a463b1bd-680d-49a3-95aa-3e1df2ec68e5'), ('751221ff-c173-443f-a7d1-1f5ffe3f0218'),
  ('e1078af6-fad1-40f9-97df-d45565faab85'), ('6307d67e-1bd4-4338-a94b-0a407cfe9621'), ('3f931b00-bff6-418d-b683-c4416d27809a'),
  ('9e8ce20e-aa92-4139-a176-3a2ebb45496b'), ('57234988-6c63-4f61-82f3-23a433f953a8'), ('71f1d262-23ae-4d83-aa5f-0d5061f812f4'),
  ('2e197c36-ffd8-43ae-a757-0659b60fb29a'), ('9ac84f5f-bc3e-45c7-918d-f9f3f94821bd'), ('fccb4a23-2768-4755-9744-f4ea64274df2'),
  ('44e0f286-14b8-47af-80e2-df7ac7a7f7d0'), ('d53bca07-c8b3-45c3-8e43-2b67f6b416a0'), ('58b61d17-61c6-4fd3-9cf0-7fc2f3e30a71'),
  ('c86e96c1-180f-458e-a7fc-2035d16fde40'), ('c94251ae-fe9d-40fb-a6d8-d8a0806b4a31'), ('eaa0ccc5-f3ec-4b80-bfae-16ef546baed5'),
  ('0b109db4-c11e-4d9c-9aeb-f3a5e68b8bb0'), ('e62098f3-de44-4881-bb10-355f14531908'), ('03fcead7-ed0d-422c-93b1-06d2c7b513cc'),
  ('11b855ce-4020-4c38-ae44-895a8d9586ff'), ('3e8bce38-9f0d-49cf-a5e6-2ea325ef365a'), ('2f26955e-acf2-482b-b7b9-eb873fe902bf'),
  ('f0f6f004-2edf-4a0c-b932-021a7ccfa6b8'), ('b6d5aa0a-a02d-48aa-b56d-36a37a786d0e'), ('07fe6068-ee7c-45b0-99c0-1385310bdad9'),
  ('143b9774-0769-4830-962f-46f7978b5210'), ('de816c68-3b4d-4884-898c-c6a514e76e8e');

do $$
declare renames int; prisons int;
begin
  select count(*) into renames from library_names n join public.venues v on v.id = n.id
    where v.category = 'library' and v.public_visible and btrim(v.venue_name) = n.old_name;
  select count(*) into prisons from prison_libraries p join public.venues v on v.id = p.id
    where v.category = 'library' and v.public_visible and btrim(v.venue_name) ~* '\m(hmp|prison|yoi)\M';
  if renames <> 45 or prisons <> 35 then
    raise exception 'Expected 45 renames and 35 public prison libraries, found % and %. The data changed after 22 Oct; re-check before running.', renames, prisons;
  end if;
end $$;

update public.venues v set
  venue_name = n.new_name,
  notes = concat_ws(' ', nullif(btrim(v.notes), ''), 'Display name corrected 2026-10-22 at owner request (#92); source name "' || n.old_name || '".')
from library_names n where v.id = n.id;

update public.venues v set
  public_visible = false,
  review_reason = concat_ws(' ', nullif(btrim(v.review_reason), ''), 'Owner decision 2026-10-22: not open to the public (prison or young offender institution library); record kept (#92).')
from prison_libraries p where v.id = p.id;

-- Expect 45 renamed and 35 hidden.
select (select count(*) from public.venues where notes like '%Display name corrected 2026-10-22 at owner request (#92)%') as renamed,
       (select count(*) from public.venues where not public_visible and review_reason like '%Owner decision 2026-10-22: not open to the public%') as prisons_hidden;
commit;

-- Rollback: restore the source names and republish the prison libraries, for rows this file changed.
-- update public.venues set
--   venue_name = substring(notes from 'Display name corrected 2026-10-22 at owner request \(#92\); source name "([^"]*)"\.'),
--   notes = nullif(btrim(regexp_replace(notes, '\s*Display name corrected 2026-10-22 at owner request \(#92\); source name "[^"]*"\.', '')), '')
-- where notes like '%Display name corrected 2026-10-22 at owner request (#92)%';
-- update public.venues set public_visible = true,
--   review_reason = nullif(btrim(replace(review_reason, 'Owner decision 2026-10-22: not open to the public (prison or young offender institution library); record kept (#92).', '')), '')
-- where review_reason like '%Owner decision 2026-10-22: not open to the public%';

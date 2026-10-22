-- Owner decision, 22 October 2026 (#92): archives, record offices and local-history centres listed
-- as libraries are research services, not family libraries, so they are hidden from public listings.
-- Records are kept, not deleted, and stay out of the operations review queue. 58 rows, each pinned by
-- id and current name; the run stops if any has changed since 22 Oct. Libraries whose name says
-- "Library" are not touched, even if they also hold archives.
begin;
-- No library row is review-locked today; this keeps the change applying if one becomes so.
set local dadspace.review_write = 'on';

create temp table archive_libraries(id uuid primary key, name text not null) on commit drop;
insert into archive_libraries values
  ('c990817e-0936-415f-a663-26089b6a7e82', 'Archive Service'),
  ('3ca44416-6012-4d25-ab52-c517a3cca519', 'Archives'),
  ('771b8db6-7017-4507-a276-e1deac294da6', 'Archives'),
  ('5001ef73-2c20-475f-9e13-840145c53388', 'Archives'),
  ('77ae0af9-468d-48d6-9925-52677c8a6cb0', 'Archives and Local Studies'),
  ('378a0440-6a0e-4095-af5c-0080647ddfeb', 'Archives Service'),
  ('005310da-58f0-4ebe-a96f-843ed5022500', 'Archives: Wigan & Leigh'),
  ('af5e7d2c-c878-4a1a-8c8b-940254bcdef5', 'Barrow Archive Centre'),
  ('fb8814a1-f8f9-4083-8104-bfb919320e14', 'Bath Record Office'),
  ('0c49921d-aff7-4148-94a5-efb0b777fdf2', 'Berkshire Record Office'),
  ('4c039ff0-ab2e-46c9-9898-4b0cad0fd85a', 'Birmingham Archive'),
  ('23f78ad1-4103-45c4-b611-98924a74aac2', 'Buckinghamshire Archives'),
  ('d0f3a60f-821e-4209-be54-88fab1487673', 'Cambridgeshire Archives'),
  ('3bf83ed1-7f3b-4c37-8db0-d08182e24af2', 'Carlisle Archive Centre'),
  ('ef5743a8-1c92-49e1-bf6e-40ebd412c72a', 'Cheshire Archives and Local Studies'),
  ('a6c1359a-39a0-44f1-9a43-9628e91d68eb', 'Croydon Archives Service'),
  ('4ec88381-c615-4d44-a395-cfcdbcf75faf', 'Derbyshire Record Office'),
  ('95f64c08-c244-4ec3-873f-e6672a449115', 'Dorset History Centre'),
  ('ae664907-1103-4747-a983-fb404f839754', 'Dudley Archives and Local History Centre'),
  ('a2cddb9a-14f2-415f-b148-6cd987353582', 'Durham County Record Office'),
  ('300f5f5d-c38e-4931-b313-929ab52868f1', 'Family & Local History Centre'),
  ('dd1c28b4-9c4e-43b7-a166-b93397de14ba', 'Gloucestershire Archives'),
  ('70c34642-4c81-44c9-bd24-6d318a649284', 'Gosport Naval & Local Studies'),
  ('25becea9-ab18-422e-bad8-15a705587f2d', 'Hampshire Archives and Local Studies'),
  ('c810062d-fdb0-4d0b-9f59-684c8787d2ec', 'Haringey Archive and Local History'),
  ('16876908-6860-419b-b3ec-9ac93c7171eb', 'Harrow Local History Collection and Archive'),
  ('9f10ad83-8f86-4ff1-bb4b-be97ed58d66f', 'Hertfordshire Archives & Local Studies'),
  ('daa861cd-ac58-4844-bb71-d5f808133bf0', 'History Centre'),
  ('c2f4c224-6a95-46d8-a7ab-1eb0be3e587e', 'Keighley Local Studies & Archives'),
  ('cfeeb90b-08f0-42bb-ac25-930ceb0aa5b0', 'Kendal Archive Centre'),
  ('d11192b0-2855-4e9b-8701-a55fb8567505', 'Kent Archives'),
  ('ea542f8c-412b-47ae-851e-60d9c5149b65', 'Kingston History Centre'),
  ('56a85ebe-7f1a-41c1-8e5d-785afb5d0647', 'Lancashire Archives'),
  ('9b4a6cdc-69b2-4634-a9c5-ea5b84287e8d', 'Leicestershire, Leicester and Rutland Record Office'),
  ('a50f022b-e6f2-4ca6-9034-90d0c2637a5d', 'Leigh Local Studies'),
  ('c7f115d0-c404-4205-8f6e-3a7bb8e345bc', 'Local history and archives'),
  ('2531b47e-ee47-4c19-8de4-283205172d45', 'Local History and Archives'),
  ('494a49c1-4591-4fa4-b8b3-ffeda5e85eaf', 'Local Studies'),
  ('ddeb662d-ffb9-4001-89d2-aefc556ac65e', 'Local Studies and Archives'),
  ('a52e683c-2ec2-4015-98ab-6b38ebc597a5', 'Local Studies Centre'),
  ('c7c0dfed-b633-4b61-9747-c19a5c092b0f', 'Medway Archives'),
  ('678543bf-c4bf-49c0-9d7c-3a7b9778ab23', 'Norfolk Heritage Centre'),
  ('0385a20e-804e-4049-bfdb-fd55dd315cfa', 'Norfolk Record Office'),
  ('f562395d-0707-4441-8ba5-921f7165a5dc', 'Nottinghamshire Archives'),
  ('1379b98c-a552-4459-844b-87f7ada02354', 'Oxfordshire History Centre'),
  ('03658e38-42df-415c-a949-318efe1c4196', 'St Helens Archive Service'),
  ('9eee9939-f1d3-4b0e-8415-d9391d1da885', 'Stoke-on-Trent Archives'),
  ('38ce50e4-40ab-4901-9015-a6acde089ac6', 'Surrey History Centre'),
  ('dbb7efb1-73b7-461b-9b2c-e75a158c019d', 'Sutton Central Archive and Local Studies'),
  ('e7e77b41-fc7d-4984-95c6-03d0a5d55a41', 'The ARK (Knowsley Archives Service)'),
  ('64d9f284-9d96-4117-8a63-e83c8346505f', 'Trafford Local Studies'),
  ('e6a7e946-03b2-48e0-8379-76ab0686266d', 'Wandsworth Heritage Service'),
  ('c047d85a-7117-40ac-8c01-63c25041ec6f', 'West Sussex Record Office'),
  ('03ad08d5-f4f1-4362-a65b-8afef865d7dd', 'West Yorkshire Archive Service'),
  ('09ad10ea-40b6-4ad8-934d-c77e42ecfb31', 'Whitehaven Archive & Local Studies Centre'),
  ('4c570fee-1f26-4144-9465-173dbcf00968', 'Wigan Local Studies'),
  ('38ea7bc4-6960-4081-bb43-5c352055f6cc', 'Wirral Archives'),
  ('fd41dcd8-1e30-45b6-aed3-4879cc21f422', 'WYAS  -Calderdale (located in CL Halifax)');

do $$
declare n int;
begin
  select count(*) into n from archive_libraries a join public.venues v on v.id = a.id
    where v.category = 'library' and v.public_visible and btrim(v.venue_name) = a.name;
  if n <> 58 then
    raise exception 'Expected 58 public archive libraries, found %. The data changed after 22 Oct; re-check before running.', n;
  end if;
end $$;

update public.venues v set
  public_visible = false,
  review_reason = concat_ws(' ', nullif(btrim(v.review_reason), ''), 'Owner decision 2026-10-22: archive or record office, not a family library; record kept (#92).')
from archive_libraries a where v.id = a.id;

-- Expect 58.
select count(*) as archives_hidden from public.venues
where not public_visible and review_reason like '%Owner decision 2026-10-22: archive or record office%';
commit;

-- Rollback: republish the archives this file hid.
-- update public.venues set public_visible = true,
--   review_reason = nullif(btrim(replace(review_reason, 'Owner decision 2026-10-22: archive or record office, not a family library; record kept (#92).', '')), '')
-- where review_reason like '%Owner decision 2026-10-22: archive or record office%';

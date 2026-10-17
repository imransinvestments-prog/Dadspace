begin;
do $$
 declare a uuid:=gen_random_uuid(); b uuid:=gen_random_uuid(); actor uuid:=gen_random_uuid(); req uuid:=gen_random_uuid(); aid uuid; rid uuid; p jsonb; plan jsonb; source_id uuid:=gen_random_uuid();
begin
 if has_function_privilege('anon','public.dadspace_review_apply_v2(uuid,uuid,text,uuid,uuid,text,text,jsonb)','execute') or has_function_privilege('authenticated','public.dadspace_review_plan_v2(text,uuid,uuid,jsonb)','execute') then raise exception 'V2 API exposed'; end if;
 insert into public.venues(id,venue_name,category,address,postcode,country,source_url,public_visible) values(a,'Old name','library','1 High Street','W4 2AB','England','https://example.com/a',false),(b,'Public branch','library','2 High Street','W4 2AB','England','https://example.com/b',true);
 insert into public.venue_sources(id,venue_id,source_name,source_record_id) values(source_id,a,'V2 fixture',a::text);
 p:='{"changes":{"venue_name":"Correct name","category":"nursery","website":"https://example.com/branch","access":"customers"},"source_url":"https://example.com/evidence"}';
 plan:=public.dadspace_review_plan_v2('edit',a,null,p);
 aid:=public.dadspace_review_apply_v2(actor,req,'edit',a,null,plan->>'fingerprint','Evidenced factual correction, keeping publication unchanged',p);
 if not exists(select 1 from public.venues where id=a and venue_name='Correct name' and category='nursery' and website='https://example.com/branch' and access='customers' and country='England' and not public_visible) then raise exception 'Edit readback failed'; end if;
 if aid<>public.dadspace_review_apply_v2(actor,req,'edit',a,null,plan->>'fingerprint','Evidenced factual correction, keeping publication unchanged',p) then raise exception 'Edit repeated'; end if;
 begin
  perform public.dadspace_review_apply_v2(actor,req,'edit',a,null,plan->>'fingerprint','Evidenced factual correction, keeping publication unchanged',jsonb_set(p,'{changes,venue_name}','"Different name"'));
  raise exception 'Expected request patch mismatch';
 exception when raise_exception then if sqlerrm not like 'Request identity already used%' then raise; end if; end;
 update public.venues set venue_name='Bad import',category='playground',access='yes',website='https://example.com/wrong' where id=a;
 if not exists(select 1 from public.venues where id=a and venue_name='Correct name' and category='nursery' and access='customers' and website='https://example.com/branch') then raise exception 'Import lost reviewed facts'; end if;
 begin
  perform public.dadspace_review_plan('rollback',aid,null);raise exception 'Expected legacy rollback refusal';
 exception when raise_exception then if sqlerrm not like 'Rollback unavailable%' then raise; end if; end;
 begin
  update public.venue_sources set source_record_id='Changed source evidence' where id=source_id;
  perform public.dadspace_review_plan_v2('rollback',aid,null,'{}');raise exception 'Expected changed source rollback refusal';
 exception when raise_exception then if sqlerrm not like 'Records changed after decision%' then raise; end if; end;
 plan:=public.dadspace_review_plan_v2('rollback',aid,null,'{}');
 rid:=public.dadspace_review_apply_v2(actor,gen_random_uuid(),'rollback',aid,null,plan->>'fingerprint','Restore original facts after checking unchanged evidence','{}');
 if not exists(select 1 from public.venues where id=a and venue_name='Old name' and category='library' and access is null and website is null and country='England' and not public_visible) then raise exception 'Factual rollback failed'; end if;
 if not exists(select 1 from public.operations_review_audit where id=aid and requested_patch=p and before_fields->>'venue_name'='Old name' and after_fields->>'venue_name'='Correct name' and reverted_by=rid) then raise exception 'Factual audit missing'; end if;
 for p in select value from jsonb_array_elements('[{"changes":{"country":"Wales"},"source_url":"https://example.com"},{"changes":{"address":"New address"},"source_url":"https://example.com"},{"changes":{"latitude":91,"longitude":0},"source_url":"https://example.com"},{"changes":{"website":"javascript:alert(1)"},"source_url":"https://example.com"}]'::jsonb) loop
  begin
   perform public.dadspace_review_plan_v2('edit',a,null,p);raise exception 'Expected invalid patch refusal';
  exception when raise_exception then if sqlerrm='Expected invalid patch refusal' then raise; end if; end;
 end loop;
 p:='{"changes":{"address":"Verified new address","latitude":null,"longitude":null},"source_url":"https://example.com/evidence"}';
 plan:=public.dadspace_review_plan_v2('edit',a,null,p);
 perform public.dadspace_review_apply_v2(actor,gen_random_uuid(),'edit',a,null,plan->>'fingerprint','Correct address and explicitly clear unknown coordinates',p);
 if not exists(select 1 from public.venues where id=a and address='Verified new address' and latitude is null and longitude is null) then raise exception 'Location correction failed'; end if;
 plan:=public.dadspace_review_plan_v2('reject',b,null,'{}');
 perform public.dadspace_review_apply_v2(actor,gen_random_uuid(),'reject',b,null,plan->>'fingerprint','Reject this independently checked unsuitable candidate','{}');
 if not exists(select 1 from public.venues where id=b and not public_visible and discovery_status='rejected') then raise exception 'Reject failed'; end if;
 plan:=public.dadspace_review_plan_v2('hide',b,null,'{}');
 perform public.dadspace_review_apply_v2(actor,gen_random_uuid(),'hide',b,null,plan->>'fingerprint','Temporary visibility hold while evidence is checked','{}');
 if not exists(select 1 from public.venues where id=b and discovery_status='hidden') then raise exception 'Hide/reject distinction failed'; end if;
 perform set_config('dadspace.review_write','on',true);
 update public.venues set category='Children’s playground',access='customers' where id=b;
 perform set_config('dadspace.review_write','off',true);
 begin
  perform public.dadspace_review_plan_v2('approve',b,null,'{}');raise exception 'Expected restricted playground refusal';
 exception when raise_exception then if sqlerrm not like 'Restricted playground%' then raise; end if; end;
 perform set_config('dadspace.review_write','on',true);
 update public.venues set category='Museum' where id=b;
 perform set_config('dadspace.review_write','off',true);
 plan:=public.dadspace_review_plan_v2('approve',b,null,'{}');
 perform public.dadspace_review_apply_v2(actor,gen_random_uuid(),'approve',b,null,plan->>'fingerprint','Customers are allowed for other venue types under settled policy','{}');
 begin
  perform public.dadspace_review_plan_v2('edit',b,null,'{"changes":{"category":"playground"},"source_url":"https://example.com/evidence"}');raise exception 'Expected public restrictive-edit refusal';
 exception when raise_exception then if sqlerrm not like 'Restricted playground%' then raise; end if; end;
 insert into public.venue_sources(venue_id,source_name,source_record_id,source_payload) values(b,'Dadspace reviewed classification',b::text,'{"accepted":true,"public_visible":false}');
 begin
  perform public.dadspace_review_plan_v2('approve',b,null,'{}');raise exception 'Expected reviewed-classification hold refusal';
 exception when raise_exception then if sqlerrm not like 'Existing classification hold%' then raise; end if; end;
end $$;
rollback;

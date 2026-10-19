begin;
do $$
declare v uuid:=gen_random_uuid(); actor uuid:=gen_random_uuid(); aid uuid; plan jsonb; patch jsonb;
begin
 insert into public.venues(id,venue_name,source_url,opening_hours,fee) values(v,'Visitor facts fixture','https://example.com/branch','Original hours','Original fee');
 patch:='{"changes":{"opening_hours":"Mon–Fri 10:00–17:00; holidays check operator","fee":"Library entry free; service charges may apply"},"source_url":"https://example.com/branch"}';
 plan:=public.dadspace_review_plan_v2('edit',v,null,patch);
 aid:=public.dadspace_review_apply_v2(actor,gen_random_uuid(),'edit',v,null,plan->>'fingerprint','Visitor facts checked against the official branch page',patch);
 if public.dadspace_public_venue_visitor_info(v) is not null then raise exception 'Hidden evidence leaked'; end if;
 if has_function_privilege('anon','public.dadspace_public_venue_visitor_info(uuid)','execute') or has_function_privilege('authenticated','public.dadspace_public_venue_visitor_info(uuid)','execute') then raise exception 'Visitor evidence RPC exposed'; end if;
 if not exists(select 1 from public.venues where id=v and opening_hours=patch->'changes'->>'opening_hours' and fee=patch->'changes'->>'fee' and not public_visible) then raise exception 'Visitor facts edit failed'; end if;
 update public.venues set opening_hours='Bad import',fee='Bad import' where id=v;
 if not exists(select 1 from public.venues where id=v and opening_hours=patch->'changes'->>'opening_hours' and fee=patch->'changes'->>'fee') then raise exception 'Import overwrote reviewed visitor facts'; end if;
 plan:=public.dadspace_review_plan_v2('rollback',aid,null,'{}');
 perform public.dadspace_review_apply_v2(actor,gen_random_uuid(),'rollback',aid,null,plan->>'fingerprint','Restore the original visitor facts after evidence review','{}');
 if not exists(select 1 from public.venues where id=v and opening_hours='Original hours' and fee='Original fee') then raise exception 'Visitor facts inverse failed'; end if;
 -- A website-only correction must disclose its narrow review scope.
 perform set_config('dadspace.review_write','on',true);
 update public.venues set public_visible=true where id=v;
 perform set_config('dadspace.review_write','off',true);
 patch:='{"changes":{"website":"https://example.com/new-branch"},"source_url":"https://example.com/branch"}';
 plan:=public.dadspace_review_plan_v2('edit',v,null,patch);
 aid:=public.dadspace_review_apply_v2(actor,gen_random_uuid(),'edit',v,null,plan->>'fingerprint','Correct website only; visitor hours remain unverified',patch);
 if public.dadspace_public_venue_visitor_info(v)->'reviewed_fields' <> '["website"]'::jsonb then raise exception 'Website review scope lost'; end if;
 if public.dadspace_public_venue_visitor_info(v) ? 'requested_patch' then raise exception 'Private audit leaked'; end if;
 -- An audit written before this migration cannot erase the new fields.
 patch:='{"changes":{"venue_name":"Old API edit"},"source_url":"https://example.com/branch"}';
 plan:=public.dadspace_review_plan_v2('edit',v,null,patch);
 aid:=public.dadspace_review_apply_v2(actor,gen_random_uuid(),'edit',v,null,plan->>'fingerprint','Simulate an audit written before visitor facts extension',patch);
 update public.operations_review_audit set before_fields=before_fields-'opening_hours'-'fee',after_fields=after_fields-'opening_hours'-'fee' where id=aid;
 plan:=public.dadspace_review_plan_v2('rollback',aid,null,'{}');
 perform public.dadspace_review_apply_v2(actor,gen_random_uuid(),'rollback',aid,null,plan->>'fingerprint','Restore old audit without losing independent visitor fields','{}');
 if not exists(select 1 from public.venues where id=v and opening_hours='Original hours' and fee='Original fee') then raise exception 'Legacy inverse erased visitor facts'; end if;
 begin
  perform public.dadspace_review_patch(jsonb_build_object('changes',jsonb_build_object('opening_hours',repeat('x',1001)),'source_url','https://example.com'));
  raise exception 'Oversize text accepted';
 exception when raise_exception then if sqlerrm='Oversize text accepted' then raise; end if; end;
end $$;
rollback;

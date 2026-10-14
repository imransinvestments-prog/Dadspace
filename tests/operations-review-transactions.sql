begin;
do $$
declare a uuid:=gen_random_uuid(); b uuid:=gen_random_uuid(); e uuid:=gen_random_uuid(); s uuid:=gen_random_uuid(); actor uuid:=gen_random_uuid();
 req uuid:=gen_random_uuid(); aid uuid; rid uuid; plan jsonb; saved jsonb; temporary uuid:=gen_random_uuid(); n int;
begin
 if has_function_privilege('anon','public.dadspace_review_apply(uuid,uuid,text,uuid,uuid,text,text)','EXECUTE') or
  has_function_privilege('authenticated','public.dadspace_review_plan(text,uuid,uuid)','EXECUTE') or
  has_table_privilege('anon','public.operations_review_audit','SELECT') then raise exception 'Private review API is exposed'; end if;
 if not has_function_privilege('service_role','public.dadspace_review_apply(uuid,uuid,text,uuid,uuid,text,text)','EXECUTE') then raise exception 'Service API missing'; end if;
 insert into public.venues(id,venue_name,address,postcode,source_url,public_visible,discovery_status) values
 (a,'Reviewed branch','1 High Street','W4 2AB','https://example.com/a',false,'discovered'),
 (b,'Canonical branch','1 High Street','W4 2AB','https://example.com/b',true,'verified');
 insert into public.collected_events(id,title,start_date,end_date,recurrence,schedule_text,listing_type)
 values(e,'Weekly Storytime','2026-10-20','2026-10-20','recurring','Tuesday, 11–11:30, term time; holiday exclusions','activity');
 insert into public.venue_sources(id,venue_id,source_name,source_record_id) values(s,a,'Reviewed source','branch');
 plan:=public.dadspace_review_plan('approve',a,null);
 begin
  perform public.dadspace_review_apply(actor,req,'approve',a,null,'stale','Verified source, branch and location');
  raise exception 'Expected stale preview rejection';
 exception when raise_exception then if sqlerrm not like 'Preview is stale%' then raise; end if; end;
 aid:=public.dadspace_review_apply(actor,req,'approve',a,null,plan->>'fingerprint','Verified source, branch and location');
 if not (select public_visible from public.venues where id=a) then raise exception 'Approved venue not visible'; end if;
 if aid is distinct from public.dadspace_review_apply(actor,req,'approve',a,null,plan->>'fingerprint','Verified source, branch and location') then raise exception 'Duplicate request repeated'; end if;
 update public.venues set public_visible=false,venue_name='Import attempted overwrite',postcode='ZZ0 0ZZ' where id=a;
 if not (select public_visible and venue_name='Reviewed branch' and postcode='W4 2AB' from public.venues where id=a) then raise exception 'Import overwrote reviewed place'; end if;
 plan:=public.dadspace_review_plan('link',e,a);
 perform public.dadspace_review_apply(actor,gen_random_uuid(),'link',e,a,plan->>'fingerprint','Matched branch and source location evidence');
 update public.collected_events set venue_id=null where id=e;
 if (select venue_id from public.collected_events where id=e) is distinct from a then raise exception 'Repeat import lost reviewed venue link'; end if;
 select jsonb_build_object('start',start_date,'end',end_date,'recurrence',recurrence,'schedule',schedule_text,'type',listing_type) into saved from public.collected_events where id=e;
 plan:=public.dadspace_review_plan('merge',a,b);
 aid:=public.dadspace_review_apply(actor,gen_random_uuid(),'merge',a,b,plan->>'fingerprint','Confirmed duplicate branch with independent provenance');
 if (select venue_id from public.collected_events where id=e) is distinct from b or (select venue_id from public.venue_sources where id=s) is distinct from b then raise exception 'Merge lost canonical relationships'; end if;
 if not (select not public_visible and merged_into=b from public.venues where id=a) then raise exception 'Duplicate not retained hidden'; end if;
 if saved is distinct from (select jsonb_build_object('start',start_date,'end',end_date,'recurrence',recurrence,'schedule',schedule_text,'type',listing_type) from public.collected_events where id=e) then raise exception 'Merge changed opportunity evidence'; end if;
 insert into public.venue_sources(id,venue_id,source_name,source_record_id) values(temporary,a,'Repeat source','new record');
 if (select venue_id from public.venue_sources where id=temporary) is distinct from b then raise exception 'Reimport revived merged duplicate'; end if;
 begin
  perform public.dadspace_review_plan('rollback',aid,null);
  raise exception 'Expected changed rollback rejection';
 exception when raise_exception then if sqlerrm not like 'Records changed after decision%' then raise; end if; end;
 delete from public.venue_sources where id=temporary;
 plan:=public.dadspace_review_plan('rollback',aid,null);
 rid:=public.dadspace_review_apply(actor,gen_random_uuid(),'rollback',aid,null,plan->>'fingerprint','Rollback verified against unchanged decision evidence');
 if (select venue_id from public.collected_events where id=e) is distinct from a or (select venue_id from public.venue_sources where id=s) is distinct from a then raise exception 'Rollback failed to restore relationships'; end if;
 if (select reverted_by from public.operations_review_audit where id=aid) is distinct from rid then raise exception 'Rollback not audited'; end if;
 plan:=public.dadspace_review_plan('hide',a,null);
 perform public.dadspace_review_apply(actor,gen_random_uuid(),'hide',a,null,plan->>'fingerprint','Venue publication temporarily withdrawn after evidence review');
 if (select public_visible from public.venues where id=a) then raise exception 'Hide failed'; end if;
 if (select venue_id from public.collected_events where id=e) is distinct from a then raise exception 'Hide discarded useful listing'; end if;
 begin
  perform public.dadspace_review_plan('merge',b,a);
  raise exception 'Expected hidden canonical rejection';
 exception when raise_exception then if sqlerrm not like 'Choose a distinct public canonical%' then raise; end if; end;
 select count(*) into n from public.operations_review_audit where actor_id=actor;
 if n<>5 then raise exception 'Unexpected audit count: %',n; end if;
end $$;
rollback;

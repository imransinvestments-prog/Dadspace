-- Inverse for the empty-enrollment release only. Never discard adopted/new rows.
begin;
set local lock_timeout='3s';
lock table public.venues,public.collected_events,public.venue_sources,public.operations_review_audit in share row exclusive mode;
lock table public.activity_identity_sources,public.activity_identity_audit in share row exclusive mode;
do $$ declare installed public.activity_identity_installation%rowtype; begin
 select * into strict installed from public.activity_identity_installation;
 if installed.installed_fingerprint is distinct from public.dadspace_provider_install_fingerprint()
  or exists(select 1 from public.activity_identity_sources)
  or exists(select 1 from public.activity_identity_audit)
  or exists(select 1 from public.collected_events where provider_namespace is not null
            or provider_session_id is not null or provider_occurrences is not null) then
  raise exception 'Stale or nonempty identity inverse; preserve rows and prepare a reviewed inverse';
 end if;
 execute installed.original_identity;
 execute installed.original_review;
 drop trigger collected_events_set_identity on public.collected_events;
 execute installed.original_trigger;
end $$;
drop trigger provider_session_audit on public.collected_events;
drop trigger ab_provider_session_guard on public.collected_events;
drop function public.dadspace_guard_provider_session();
drop function public.dadspace_audit_provider_session();
drop function public.dadspace_listing_review_version(public.collected_events);
drop function public.dadspace_provider_install_fingerprint();
drop table public.activity_identity_audit,public.activity_identity_sources,public.activity_identity_installation;
alter table public.collected_events drop column provider_namespace,
 drop column provider_session_id, drop column provider_occurrences;
commit;

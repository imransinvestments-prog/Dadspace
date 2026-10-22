alter function public.dadspace_norm_text(text) set search_path = public, pg_temp;
alter function public.dadspace_canonical_url(text) set search_path = public, pg_temp;
alter function public.dadspace_event_identity(text,text,date,text,uuid,text,text,text) set search_path = public, pg_temp;
alter function public.dadspace_set_event_identity() set search_path = public, pg_temp;

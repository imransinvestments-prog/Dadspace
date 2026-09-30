-- Lets the events workers log under their own names so civic and activities
-- runs can be told apart in pipeline_runs. Run once in the Supabase SQL editor.
alter table public.pipeline_runs drop constraint if exists pipeline_runs_worker_check;
alter table public.pipeline_runs add constraint pipeline_runs_worker_check
  check (worker in ('news', 'events', 'events-civic', 'events-activities', 'events-all'));

-- #198 bounded read-only candidate audit, executed 18 October 2026: zero rows.
-- This is a candidate lookup, not an instruction to merge or qualify other sources.
select c.id,c.source_id,c.title,c.venue_name,c.venue_id,c.event_url,c.source_url,
       c.identity_key,c.dedupe_key,c.withdrawn_at,
       md5(to_jsonb(c)::text) as row_fingerprint
from collected_events c
where (c.title ilike 'Bounce and Rhyme and Storytime%'
       and c.venue_name in ('Southall library','Northolt library'))
   or c.event_url like 'https://ealing.events.mylibrary.digital/event?%'
order by c.id limit 100;

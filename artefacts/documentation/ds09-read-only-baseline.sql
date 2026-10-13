-- DS-09 read-only snapshot queries, 10 October 2026.
-- Run individually through the authenticated Supabase connector. No writes.
select id,name,url,category,kind,org_type,focus,nation,region,fetch_method,
       active,notes,last_checked_at,last_success_at,fail_count,last_error,
       last_event_count,source_role,source_adapter
from public.sources order by category,name;

select source_id,listing_type,count(*) as stored_count,
       count(*) filter(where venue_id is not null) as venue_linked,
       count(*) filter(where nullif(trim(schedule_text),'') is not null) as schedule_present,
       count(*) filter(where nullif(trim(location),'') is not null) as location_present,
       count(*) filter(where nullif(trim(event_url),'') is not null) as url_present,
       min(last_seen_at) as oldest_seen,max(last_seen_at) as newest_seen
from public.collected_events group by source_id,listing_type order by source_id,listing_type;

select source_id,listing_type,category,age_range,count(*) as stored_count
from public.collected_events group by source_id,listing_type,category,age_range
order by source_id,listing_type,category,age_range;

select worker,ran_at,dry_run,input_tokens,output_tokens,gemini_calls,details
from public.pipeline_runs where worker in ('events-activities','events-civic')
order by ran_at desc limit 10;

select (select count(*) from (select dedupe_key from public.collected_events
        group by dedupe_key having count(*)>1) d) as duplicate_dedupe_groups,
       (select count(*) from (select identity_key from public.collected_events
        where identity_key is not null group by identity_key having count(*)>1) i)
        as duplicate_identity_groups;

with nearby as (
 select id,category,public_visible,
  6371*2*asin(sqrt(power(sin(radians(latitude-51.466329)/2),2)
   +cos(radians(51.466329))*cos(radians(latitude))
   *power(sin(radians(longitude+0.387970)/2),2))) as km
 from public.venues
 where latitude between 51.36 and 51.57 and longitude between -0.55 and -0.23
)
select n.category,count(distinct n.id) as venues,
 count(distinct n.id) filter(where n.public_visible) as visible_venues,
 count(e.id) as stored_listings,
 count(e.id) filter(where e.listing_type='activity') as stored_activities
from nearby n left join public.collected_events e on e.venue_id=n.id
where n.km<=10 group by n.category order by n.category;

select id,source_id,title,listing_type,category,age_range,schedule_text,
       location,event_url,venue_id,start_date,end_date,last_seen_at
from public.collected_events
where location ilike any(array['%Hounslow%','%Heston%','%Feltham%','%TW4%'])
order by title;

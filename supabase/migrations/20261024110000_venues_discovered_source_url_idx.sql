-- Council discovery looks up OSM URLs already stored in venues.discovered_source_url
-- (venue_council_discovery.stored_osm_urls). Without an index that is a full scan of venues
-- (5.6s at 59k rows), and on 23 Oct 19:17 it passed the API's 8s statement timeout while the
-- other workers were writing, ending the run. source_url already has a unique index.
create index if not exists venues_discovered_source_url_idx
  on public.venues (discovered_source_url)
  where discovered_source_url is not null;

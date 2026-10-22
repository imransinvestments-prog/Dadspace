-- Database advisor housekeeping. Additive apart from one duplicate index; no rows change.
--
-- news_items had two identical btree(story_key) indexes, both created outside
-- the migration history. Keep idx_news_items_story_key (in use) and drop the
-- never-scanned copy.
drop index if exists public.news_items_story_key_idx;

-- Cover foreign keys flagged as unindexed, so deletes/updates of the referenced
-- rows and joins on these columns do not scan the referencing table.
create index if not exists idx_collected_events_superseded_by on public.collected_events (superseded_by);
create index if not exists idx_deals_source_id on public.deals (source_id);
create index if not exists idx_news_items_source_id on public.news_items (source_id);
create index if not exists idx_operations_maintenance_audit_reverted_by on public.operations_maintenance_audit (reverted_by);
create index if not exists idx_operations_review_audit_reverted_by on public.operations_review_audit (reverted_by);
create index if not exists idx_parent_discount_items_equivalent_item_id on public.parent_discount_items (equivalent_item_id);
create index if not exists idx_venues_merged_into on public.venues (merged_into);

-- Additive only: existing records and access policies are preserved.
alter table public.deals add column if not exists item_id bigint references public.parent_discount_items(id);
alter table public.parent_discount_items add column if not exists equivalent_item_id bigint references public.parent_discount_items(id);
alter table public.deal_sources add column if not exists last_verified_at timestamptz;
alter table public.deal_sources add column if not exists last_counts jsonb not null default '{}'::jsonb;
create index if not exists deals_live_verified_idx on public.deals(last_seen desc) where status='live';
create index if not exists deals_item_id_idx on public.deals(item_id);
comment on column public.deals.item_id is 'Canonical parent_discount_items identity, resolved by deterministic rules.';
comment on column public.parent_discount_items.equivalent_item_id is 'Optional canonical item identity used to collapse equivalent offers. Defaults to own id in selection.';

-- Controlled data changes applied to Dadspace on 5 October 2026.
-- Idempotent replay for an existing canonical taxonomy, after the additive migrations.
BEGIN;
UPDATE public.parent_discount_items SET uk_terms=CASE item_or_service
 WHEN 'Diaper liners' THEN 'diaper liners; nappy liners'
 WHEN 'Diaper rash cream' THEN 'diaper rash cream; nappy rash cream; rash cream; sudocrem'
 WHEN 'Diaper pail' THEN 'diaper pail; nappy pail; nappy bin; diaper bin'
 WHEN 'Diaper pail refills' THEN 'diaper pail refills; nappy pail refills; nappy bin refills; nappy bin cassettes'
 WHEN 'Baby wipes' THEN 'baby wipes; waterwipes'
 WHEN 'Bicycle' THEN 'bicycle; bike; training bike'
 WHEN 'School uniform shirts' THEN 'school uniform shirts; school shirts'
 WHEN 'School uniform polos' THEN 'school uniform polos; school polo shirts'
 WHEN 'School uniform trousers' THEN 'school uniform trousers; school trousers'
 WHEN 'School uniform skirts' THEN 'school uniform skirts; school skirts'
 WHEN 'School uniform dresses' THEN 'school uniform dresses; school dresses; school dress'
 WHEN 'School uniform sweaters' THEN 'school uniform sweaters; school jumper; school sweaters'
 WHEN 'School uniform blazers' THEN 'school uniform blazers; school blazers'
 WHEN 'School uniform shoes' THEN 'school uniform shoes; school shoes'
 ELSE uk_terms END, updated_at=now()
 WHERE item_or_service IN ('Diaper liners','Diaper rash cream','Diaper pail','Diaper pail refills','Baby wipes','Bicycle','School uniform shirts','School uniform polos','School uniform trousers','School uniform skirts','School uniform dresses','School uniform sweaters','School uniform blazers','School uniform shoes');
UPDATE public.parent_discount_items SET equivalent_item_id=(SELECT id FROM public.parent_discount_items WHERE item_or_service='Baby wipes' LIMIT 1),updated_at=now() WHERE item_or_service='Reusable wipes';
UPDATE public.parent_discount_items SET active=true,inactive_reason=null,display_group=CASE WHEN item_or_service IN ('Private tutoring','Group tutoring','Online tutoring','School tuition') THEN 'School & Learning' ELSE 'Days Out & Family Fun' END,tier='B',value_band=CASE WHEN item_or_service IN ('Family package holidays','Ski holidays') THEN 'big' ELSE 'mid' END,needs_child_evidence=true,updated_at=now()
 WHERE item_or_service IN ('Private tutoring','Group tutoring','Online tutoring','School tuition','Family package holidays','Ski holidays','Kids meals at restaurants');
UPDATE public.parent_discount_items SET uk_terms='kids meals at restaurants; kids eat free; children eat free',needs_child_evidence=false,updated_at=now() WHERE item_or_service='Kids meals at restaurants';
UPDATE public.parent_discount_items SET uk_terms=CASE WHEN uk_terms LIKE '%; family holiday; family holidays' THEN uk_terms ELSE uk_terms||'; family holiday; family holidays' END,updated_at=now() WHERE item_or_service='Family package holidays';
UPDATE public.deals d SET item_id=t.id FROM public.parent_discount_items t WHERE d.matched_item=t.item_or_service AND d.item_id IS NULL;

insert into public.deal_sources(name,source_type,url,active,notes) select 'HotUKDeals - kids bikes','rss','https://www.hotukdeals.com/rss/tag/kids-bike',true,'Validated public route 2026-10-05; free rules-only collector; source listed, not checkout verified' where not exists (select 1 from public.deal_sources where url='https://www.hotukdeals.com/rss/tag/kids-bike');
insert into public.deal_sources(name,source_type,url,active,notes) select 'HotUKDeals - school uniform','rss','https://www.hotukdeals.com/rss/tag/school-uniform',true,'Validated public route 2026-10-05; free rules-only collector; source listed, not checkout verified' where not exists (select 1 from public.deal_sources where url='https://www.hotukdeals.com/rss/tag/school-uniform');
insert into public.deal_sources(name,source_type,url,active,notes) select 'HotUKDeals - toys','rss','https://www.hotukdeals.com/rss/tag/toy',true,'Validated public route 2026-10-05; free rules-only collector; source listed, not checkout verified' where not exists (select 1 from public.deal_sources where url='https://www.hotukdeals.com/rss/tag/toy');
insert into public.deal_sources(name,source_type,url,active,notes) select 'HotUKDeals - board games','rss','https://www.hotukdeals.com/rss/tag/board-game',true,'Validated public route 2026-10-05; free rules-only collector; source listed, not checkout verified' where not exists (select 1 from public.deal_sources where url='https://www.hotukdeals.com/rss/tag/board-game');
insert into public.deal_sources(name,source_type,url,active,notes) select 'HotUKDeals - kids clothes','rss','https://www.hotukdeals.com/rss/tag/kids-clothes',true,'Validated public route 2026-10-05; free rules-only collector; source listed, not checkout verified' where not exists (select 1 from public.deal_sources where url='https://www.hotukdeals.com/rss/tag/kids-clothes');
insert into public.deal_sources(name,source_type,url,active,notes) select 'HotUKDeals - baby monitors','rss','https://www.hotukdeals.com/rss/tag/baby-monitor',true,'Validated public route 2026-10-05; free rules-only collector; source listed, not checkout verified' where not exists (select 1 from public.deal_sources where url='https://www.hotukdeals.com/rss/tag/baby-monitor');
insert into public.deal_sources(name,source_type,url,active,notes) select 'Premier Inn - kids breakfast','direct','https://www.premierinn.com/gb/en/why/food/breakfast.html',true,'Validated public route 2026-10-05; free rules-only collector; source listed, not checkout verified' where not exists (select 1 from public.deal_sources where url='https://www.premierinn.com/gb/en/why/food/breakfast.html');
insert into public.deal_sources(name,source_type,url,active,notes) select 'Halfords - children bikes','direct','https://www.halfords.com/bikes/kids-bikes/',true,'Reviewed public JSON; compare individual product price and stock; no AI' where not exists (select 1 from public.deal_sources where url='https://www.halfords.com/bikes/kids-bikes/');
COMMIT;


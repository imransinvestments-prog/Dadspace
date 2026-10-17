-- Exact three-row forward rehearsal. Application requires approved code deployed first.
BEGIN;
DO $review$ BEGIN
 PERFORM 1 FROM public.news_items n WHERE id=736 AND to_jsonb(n) @> '{"id":736,"url":"https://uk.news.yahoo.com/port-glasgow-mum-praises-2-094132002.html","title":"Port Glasgow mum praises £2 hot meal scheme as families ''can''t afford days out'' - Yahoo News UK","region":"scotland","summary":"A Port Glasgow initiative offers two-pound hot meals for local families struggling with high activity costs.","category":"activities","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"Yahoo News UK","why_it_matters":"A cheap, hot meal option for local families during days out."}'::jsonb AND published_at IS NOT DISTINCT FROM '2026-10-07T09:41:32+00:00'::timestamptz FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Stale final News row 736; abort whole batch'; END IF;
 UPDATE public.news_items SET region='scotland', geo_scope='local', geo_region=null, admin_area=null, locality='inverclyde' WHERE id=736;
END $review$;
DO $review$ BEGIN
 PERFORM 1 FROM public.news_items n WHERE id=739 AND to_jsonb(n) @> '{"id":739,"url":"https://sandbach.nub.news/news/local-news/sp14219-wand-making-dodgeball-and-glow-stick-disco-your-guide-to-half-term-holiday-fun-310364","title":"Wand making, dodgeball and glow stick disco: your guide to half-term holiday fun - Sandbach Nub News","region":"england","summary":"Sandbach offers a variety of half-term activities including wand making, dodgeball, and a glow stick disco.","category":"activities","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"Sandbach Nub News","why_it_matters":"Gives you fun local event options to keep kids busy."}'::jsonb AND published_at IS NOT DISTINCT FROM '2026-10-13T06:50:00+00:00'::timestamptz FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Stale final News row 739; abort whole batch'; END IF;
 UPDATE public.news_items SET region='england', geo_scope='local', geo_region=null, admin_area='cheshire', locality=null WHERE id=739;
END $review$;
DO $review$ BEGIN
 PERFORM 1 FROM public.news_items n WHERE id=855 AND to_jsonb(n) @> '{"id":855,"url":"https://www.gazette-news.co.uk/news/26632520.bereaved-dad-praises-maldon-support-baby-loss-week/","title":"Baby loss leaves ‘permanent scar’, says bereaved dad amid ''incredible'' support - Colchester Gazette","region":"uk","summary":"A grieving father shares his experience of baby loss and highlights the vital support available for bereaved parents.","category":"wellbeing","locality":null,"geo_scope":"nationwide","relevance":3,"admin_area":null,"geo_region":null,"source_name":"Colchester Gazette","why_it_matters":"Offers emotional validation and highlights crucial support resources for dads coping with baby loss."}'::jsonb AND published_at IS NOT DISTINCT FROM '2026-10-14T16:00:00+00:00'::timestamptz FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Stale final News row 855; abort whole batch'; END IF;
 UPDATE public.news_items SET region='england', geo_scope='local', geo_region=null, admin_area='essex', locality='maldon' WHERE id=855;
END $review$;
SELECT id,region,geo_scope,geo_region,admin_area,locality FROM public.news_items WHERE id IN (736,739,855) ORDER BY id;
ROLLBACK;

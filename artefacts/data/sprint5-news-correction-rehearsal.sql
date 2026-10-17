-- Proposed News correction rehearsal. NOT owner approval or a production apply script.
-- Full batch fails on stale selected fields. Held/no-op rows are excluded.
BEGIN;
-- 321: Nurseries should be recognised for the practical and emotional support they provide families beyond their formal roles, argues research - Nursery World
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=321 and to_jsonb(n) @> '{"id":321,"url":"https://www.nurseryworld.co.uk/content/news/nurseries-should-be-recognised-for-the-practical-and-emotional-support-they-provide-families-beyond-their-formal-roles-argues-research","title":"Nurseries should be recognised for the practical and emotional support they provide families beyond their formal roles, argues research - Nursery World","region":"uk","summary":"New research highlights that nurseries provide vital practical and emotional support to families beyond early education.","category":"parenting","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"Nursery World","why_it_matters":"Recognises the broader support network nurseries offer to struggling parents."}'::jsonb and published_at is not distinct from '2026-10-02T11:58:04+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 321; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='uk', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=321;
END $review$;

-- 328: North East play café tackling parental loneliness expands support to dads - The Northern Echo
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=328 and to_jsonb(n) @> '{"id":328,"url":"https://www.thenorthernecho.co.uk/news/26600711.guisborough-play-caf-launches-monthly-sessions-dads/","title":"North East play café tackling parental loneliness expands support to dads - The Northern Echo","region":"england","summary":"A play café in the North East is expanding its services to help tackle loneliness among dads.","category":"wellbeing","locality":null,"geo_scope":null,"relevance":4,"admin_area":null,"geo_region":null,"source_name":"The Northern Echo","why_it_matters":"Provides a welcoming space for local dads to connect and combat isolation."}'::jsonb and published_at is not distinct from '2026-10-03T04:30:00+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 328; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='local', geo_region=null, admin_area=null, locality='west_northamptonshire' WHERE id=328;
END $review$;

-- 342: More than a day out: creating fairer holidays for Cambridge children - cambridgenetwork.co.uk
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=342 and to_jsonb(n) @> '{"id":342,"url":"https://www.cambridgenetwork.co.uk/news/more-day-out-creating-fairer-holidays-cambridge-children","title":"More than a day out: creating fairer holidays for Cambridge children - cambridgenetwork.co.uk","region":"england","summary":"A Cambridge initiative aims to provide fairer access to holiday activities and trips for local children.","category":"activities","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"cambridgenetwork.co.uk","why_it_matters":"Highlights local efforts to make school holiday activities accessible for all kids."}'::jsonb and published_at is not distinct from '2026-10-02T08:55:40+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 342; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='local', geo_region=null, admin_area=null, locality='cambridge' WHERE id=342;
END $review$;

-- 362: Virgin Media gives TV customers access to kids' channels including Sky Kids, Cartoon Network, Nickelodeon and Baby TV at no extra cost throughout October - Virgin Media O2
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=362 and to_jsonb(n) @> '{"id":362,"url":"https://news.virginmediao2.co.uk/virgin-media-gives-tv-customers-access-to-kids-channels-including-sky-kids-cartoon-network-nickelodeon-and-baby-tv-at-no-extra-cost-throughout-october-2/","title":"Virgin Media gives TV customers access to kids'' channels including Sky Kids, Cartoon Network, Nickelodeon and Baby TV at no extra cost throughout October - Virgin Media O2","region":"uk","summary":"Virgin Media is giving its TV customers free access to major kids'' channels throughout October.","category":"activities","locality":null,"geo_scope":null,"relevance":4,"admin_area":null,"geo_region":null,"source_name":"Virgin Media O2","why_it_matters":"Get free premium children''s entertainment to help keep kids busy this month."}'::jsonb and published_at is not distinct from '2026-10-02T07:52:24+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 362; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='uk', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=362;
END $review$;

-- 378: Thousands of child-on-child sexual offences reported at schools in England and Wales
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=378 and to_jsonb(n) @> '{"id":378,"url":"https://www.theguardian.com/education/2026/oct/04/child-on-child-sexual-abuse-schools-england-and-wales","title":"Thousands of child-on-child sexual offences reported at schools in England and Wales","region":"england","summary":"Thousands of child-on-child sexual offences are being reported to police from schools in England and Wales.","category":"safety","locality":null,"geo_scope":null,"relevance":4,"admin_area":null,"geo_region":null,"source_name":"Guardian - Education","why_it_matters":"Highlights crucial safeguarding and safety issues affecting children in schools today."}'::jsonb and published_at is not distinct from '2026-10-04T15:00:31+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 378; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=378;
END $review$;

-- 430: Hampshire’s Top Autumn Days Out: From Owl-O-Ween to Pumpkin Time - Great British Life
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=430 and to_jsonb(n) @> '{"id":430,"url":"https://www.greatbritishlife.co.uk/magazines/hampshire/26545045.hampshires-best-autumn-halloween-events-2026/","title":"Hampshire’s Top Autumn Days Out: From Owl-O-Ween to Pumpkin Time - Great British Life","region":"england","summary":"Explore Hampshire''s best autumn family events, featuring owl displays and pumpkin-themed activities.","category":"activities","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"Great British Life","why_it_matters":"Offers fun autumn day out ideas for families based in Hampshire."}'::jsonb and published_at is not distinct from '2026-10-04T11:00:00+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 430; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='local', geo_region=null, admin_area='hampshire', locality=null WHERE id=430;
END $review$;

-- 474: Inheritance tax: Expert says when parents should give money early - AOL.com
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=474 and to_jsonb(n) @> '{"id":474,"url":"https://www.aol.co.uk/articles/inheritance-tax-expert-says-parents-123000000.html","title":"Inheritance tax: Expert says when parents should give money early - AOL.com","region":"uk","summary":"An expert explains the rules and benefits of parents gifting money early to children to manage inheritance tax.","category":"money","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"AOL.com","why_it_matters":"Useful advice if you are planning your family''s long-term financial future."}'::jsonb and published_at is not distinct from '2026-10-06T12:30:47+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 474; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='uk', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=474;
END $review$;

-- 486: OakNorth Enters Children's Savings Market with 3.5% Junior Cash ISA and Bubble Partnership - FF News
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=486 and to_jsonb(n) @> '{"id":486,"url":"https://ffnews.com/news/oaknorth-launches-junior-cash-isa-offering-3-5-aer-and-partners-with-childcare-a-48c6d2b9","title":"OakNorth Enters Children''s Savings Market with 3.5% Junior Cash ISA and Bubble Partnership - FF News","region":"uk","summary":"OakNorth has launched a Junior Cash ISA offering 3.5% interest in partnership with childcare app Bubble.","category":"money","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"FF News","why_it_matters":"A new savings option to help you build a nest egg for your child."}'::jsonb and published_at is not distinct from '2026-10-05T13:55:49+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 486; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='uk', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=486;
END $review$;

-- 596: Foundation Holiday Courses return for October half-term - Foundation of Light
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=596 and to_jsonb(n) @> '{"id":596,"url":"https://foundationoflight.co.uk/news/foundation-holiday-courses-return-for-october-half-term/","title":"Foundation Holiday Courses return for October half-term - Foundation of Light","region":"england","summary":"The Foundation of Light is running sports and activity courses for children during the October half-term.","category":"activities","locality":null,"geo_scope":null,"relevance":4,"admin_area":null,"geo_region":null,"source_name":"Foundation of Light","why_it_matters":"Keeps kids active and entertained locally during the school holidays."}'::jsonb and published_at is not distinct from '2026-10-08T16:41:06+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 596; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='local', geo_region=null, admin_area=null, locality='sunderland' WHERE id=596;
END $review$;

-- 630: County Durham young dad says more support needed for new fathers - BBC
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=630 and to_jsonb(n) @> '{"id":630,"url":"https://www.bbc.co.uk/news/articles/ckgel90yzvjdo","title":"County Durham young dad says more support needed for new fathers - BBC","region":"england","summary":"A young father from County Durham is campaigning for better mental health and practical support for new dads.","category":"wellbeing","locality":"county_durham","geo_scope":"local","relevance":4,"admin_area":null,"geo_region":null,"source_name":"BBC","why_it_matters":"Emphasises the need for improved local support networks for new fathers."}'::jsonb and published_at is not distinct from '2026-10-11T07:56:31+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 630; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=630;
END $review$;

-- 653: Bereaved Silsden dad hopes to educate school children on mental health - Rayo
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=653 and to_jsonb(n) @> '{"id":653,"url":"https://www.hellorayo.co.uk/greatest-hits/west-yorkshire/news/dad-of-teen-wants-to-educate-children-on-mental-health-after-sons-death","title":"Bereaved Silsden dad hopes to educate school children on mental health - Rayo","region":"england","summary":"A bereaved dad from Silsden is visiting local school children to raise awareness about mental health support.","category":"health","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"Rayo","why_it_matters":"Highlights local school mental health initiatives and emotional wellbeing support for kids."}'::jsonb and published_at is not distinct from '2026-10-09T06:10:59+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 653; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=653;
END $review$;

-- 708: Children offered free entry into former National Trust site on these dates - malverngazette.co.uk
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=708 and to_jsonb(n) @> '{"id":708,"url":"https://news.google.com/rss/articles/CBMiqAFBVV95cUxPNWJzLVF2N25mSzBqLUZJV0dCNzNLTkRYNzZnR2E2SnFpRUQyQ0RiZEpFZnllRjlfVHh4QkF1U1Q3YTJHemRISl9UWDJhV1hTNF9FeF9pTGlvemQ4dEZPSlhEbVQwYTFULWFRU1V0bWxQTDNaZ0FyRkJaU2pFczZPNVMwVWo5dW9DQk5uUkh4WVdYN1hWWElFWEtQNHItenRWblVoWXBhVWo?oc=5","title":"Children offered free entry into former National Trust site on these dates - malverngazette.co.uk","region":"england","summary":"Children are being offered free entry on selected dates to a former National Trust property.","category":"activities","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"malverngazette.co.uk","why_it_matters":"A budget-friendly heritage day out option for families."}'::jsonb and published_at is not distinct from '2026-10-12T11:00:00+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 708; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='local', geo_region=null, admin_area=null, locality='redditch' WHERE id=708;
END $review$;

-- 808: Small Swansea free museum with just three staff is named best in UK - Wales Online
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=808 and to_jsonb(n) @> '{"id":808,"url":"https://www.walesonline.co.uk/whats-on/family-kids-news/small-swansea-free-museum-just-34757151","title":"Small Swansea free museum with just three staff is named best in UK - Wales Online","region":"wales","summary":"A small, free museum in Swansea has been named the best in the UK.","category":"activities","locality":"swansea","geo_scope":"local","relevance":3,"admin_area":null,"geo_region":null,"source_name":"Wales Online","why_it_matters":"A great free option for an educational family day out in Wales."}'::jsonb and published_at is not distinct from '2026-10-13T13:39:48+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 808; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='wales', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=808;
END $review$;

-- 877: More than 40% off Alton Towers tickets with these discount codes - The Independent
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=877 and to_jsonb(n) @> '{"id":877,"url":"https://www.independent.co.uk/deals/alton-towers-discount-code-b2705011.html","title":"More than 40% off Alton Towers tickets with these discount codes - The Independent","region":"england","summary":"Discount deals offer more than 40% off entry tickets to Alton Towers theme park.","category":"activities","locality":null,"geo_scope":null,"relevance":4,"admin_area":null,"geo_region":null,"source_name":"The Independent","why_it_matters":"Saves money on tickets for a popular theme park outing."}'::jsonb and published_at is not distinct from '2026-10-12T13:11:32+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 877; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='england', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=877;
END $review$;

-- 306: Mum petitions UK Parliament for paid breastfeeding breaks at work - AOL.com
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=306 and to_jsonb(n) @> '{"id":306,"url":"https://www.aol.co.uk/articles/mum-petitions-uk-parliament-paid-042457000.html","title":"Mum petitions UK Parliament for paid breastfeeding breaks at work - AOL.com","region":"uk","summary":"A petition calls on the UK Parliament to introduce statutory paid breastfeeding breaks for working mothers.","category":"policy","locality":null,"geo_scope":null,"relevance":4,"admin_area":null,"geo_region":null,"source_name":"AOL.com","why_it_matters":"This proposed change would help support your partner when returning to work after maternity."}'::jsonb and published_at is not distinct from '2026-10-02T04:24:00+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 306; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='uk', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=306;
END $review$;

-- 453: Accredited official statistics: Education and training statistics for the UK: 2026
DO $review$ BEGIN
  PERFORM 1 FROM public.news_items n WHERE id=453 and to_jsonb(n) @> '{"id":453,"url":"https://www.gov.uk/government/statistics/announcements/education-and-training-statistics-for-the-uk-2026","title":"Accredited official statistics: Education and training statistics for the UK: 2026","region":"uk","summary":"The DfE has published comprehensive statistics on UK schools, pupil attainment, qualifications, and education spending.","category":"education","locality":null,"geo_scope":null,"relevance":3,"admin_area":null,"geo_region":null,"source_name":"GOV.UK - Department for Education","why_it_matters":"Gives a broad overview of the state of UK education and school standards."}'::jsonb and published_at is not distinct from '2026-10-06T12:22:30+00:00'::timestamptz FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Stale/missing News row 453; entire batch must be re-reviewed'; END IF;
  UPDATE public.news_items n SET region='uk', geo_scope='nationwide', geo_region=null, admin_area=null, locality=null WHERE id=453;
END $review$;
SELECT id,region,geo_scope,geo_region,admin_area,locality FROM public.news_items WHERE id IN (321,328,342,362,378,430,474,486,596,630,653,708,808,877,306,453) ORDER BY id;
ROLLBACK;

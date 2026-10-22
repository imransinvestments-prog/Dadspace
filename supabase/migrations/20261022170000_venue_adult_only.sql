-- Audience flag for venues where age policy decides family suitability (owner request,
-- 22 October 2026; first used for amusement arcades). Three states, never guessed:
--   true  = evidence the venue is for adults only (e.g. an Adult Gaming Centre registration)
--   false = evidence that children are admitted (e.g. a family entertainment centre)
--   null  = no evidence either way yet
-- adult_only_evidence records the source of the decision.
alter table public.venues add column if not exists adult_only boolean;
alter table public.venues add column if not exists adult_only_evidence text;
comment on column public.venues.adult_only is 'true adults only, false children admitted, null no evidence yet; see adult_only_evidence';

-- Owner rule, 22 October 2026: amusement arcades reach family discovery only when confirmed
-- family-friendly, and the owner reviews only those the evidence could not decide.
--   adult_only = true   never published
--   adult_only = false  publishable (evidence already decided)
--   adult_only is null  publishable only through an owner review, which records the decision
-- Applies to every write path (review actions, manual SQL, importers). Run after
-- 20261022170000_venue_adult_only.sql.
create or replace function public.dadspace_arcade_publication_guard()
returns trigger language plpgsql set search_path = '' as $$
begin
  if new.category = 'Amusement arcade' and new.public_visible
     and (tg_op = 'INSERT' or not coalesce(old.public_visible, false)) then
    if new.adult_only then
      raise exception 'Adult-only arcade cannot be published to family discovery';
    end if;
    if new.adult_only is null then
      if coalesce(current_setting('dadspace.review_write', true), 'off') <> 'on' then
        raise exception 'Arcade age policy undecided: publish it through an owner review';
      end if;
      -- Approving an undecided arcade is the owner's family-friendly decision.
      new.adult_only := false;
      new.adult_only_evidence := concat_ws(' ', new.adult_only_evidence,
        'Owner review approved as family-friendly on ' || to_char(now() at time zone 'Europe/London', 'YYYY-MM-DD') || '.');
    end if;
  end if;
  return new;
end $$;
revoke all on function public.dadspace_arcade_publication_guard() from public, anon, authenticated, service_role;

drop trigger if exists venues_arcade_publication_guard on public.venues;
create trigger venues_arcade_publication_guard before insert or update on public.venues
  for each row execute function public.dadspace_arcade_publication_guard();

# Venue publication cleanup, 14 October 2026

Owner scope: remove adult gaming/casino listings from arcades, hide parks explicitly marked private, and remove indoor/outdoor filters for now. Records remain in the database; this changes publication, not place identity.

## Data review and changes

Screened all 601 arcade records against current source tags and the Gambling Commission premises register downloaded on 14 October. Reviewed register name/postcode matches, selected address matches, explicit minimum ages and operator evidence. This is a screening pass, not independent certification of all retained arcades.

- 78 records hidden on adult-gaming register matches, explicit 18+/21+ tags or operator age restrictions. An AGC registration does not by itself prove the entire establishment is adult-only: those records are withheld from general family discovery pending contrary family-access evidence.
- 2 casino-named records quarantined at the owner's request pending sufficient family-access evidence: Casino, Scarborough, and Casino Leisure, Devizes. Neither is asserted to be confirmed adult-only.
- 21 records retained with matching family entertainment or operator evidence, including Grand Casino, Penzance, and Slots of Fun, Blackpool. Separate adult sections may exist.
- 500 records retained as unverified, not certified as family suitable. Missing register matches do not prove suitability. Nearby betting shops do not establish an arcade's identity.
- 1,659 private playgrounds hidden. These are the parks/play areas present in the dataset with `access=private`. `customers`, `permissive`, `restricted`, `yes` and unknown access are outside this change.

Every arcade decision and its evidence is in `artefacts/data/venue-publication-review-2026-10-14.json`. The Commission warns that its register includes applications and may be incomplete; it is used as evidence, not as an infallible live licence status feed.

`supabase/venue-publication-cleanup.sql` is the exact transaction applied to project `ebebkbrdqmceckmhlcpw`. It changes only previously visible, matching records, appends review reasons and records review time. It is not a schema migration and does not delete records. A snapshot of the 1,739 previous visibility/review states was saved locally before execution for selective rollback. Do not blindly republish records with subsequent reviews.

## Verification

Production database after the transaction: 57,232 public venues; 521 public arcades; zero selected excluded arcades or explicitly private parks still visible. Reels search through the deployed `nearby_venue_page` RPC returns zero. Grand Casino and Slots of Fun remain visible. All public discovery paths use the existing `public_visible` gate, including homepage RPCs, directory search, public detail reads and photos.

The UI removes Rainy-day proof and Outdoors toggles. The API ignores stale indoor/outdoor query parameters and always passes false for both legacy RPC flags. Free entry, location, category, search and pagination remain available. No capability fields or guessed backfill are introduced; restoring these filters requires evidenced data and is deferred.

Local verification: 28 Node regression tests and TypeScript check pass. The new regression checks stale filter URLs and verifies that hidden adult-gaming records stay hidden while a family arcade with Casino in its name remains readable. Local Next build is blocked by Windows filesystem access errors in SWC; Linux PR CI must pass before merging.

## Owner follow-up: no or missing access and events hero scope

The owner subsequently requested hiding the remaining parks/playgrounds with `access=no` or missing access. `supabase/venue-access-cleanup.sql` applies this separate publication transaction. Before execution, a local rollback snapshot saved all 37,761 IDs and their previous visibility/review values (all were visible with null review reason/time).

Additional records hidden: 41 playgrounds with `access=no`; 37,145 playgrounds, 188 theme parks, 112 water parks and 275 animal parks with missing access. Unknown access is a hold pending evidence, not confirmation of private or restricted access. Existing `customers`, `permissive`, `restricted` and `yes` records remain outside this follow-up. No records or source evidence were deleted.

Production verification after the follow-up: 19,471 public venues, including 10,213 parks/playgrounds; zero public parks/playgrounds with private, no, blank or missing access. This deliberately reduces public coverage substantially under the owner's requested publication policy.

For #99, the Events hero now labels both counts as UK-wide listings and explicitly says that the counts do not change with the location or filters below. Counts still describe the national server read; they are not presented as Cardiff or another selected location's results. The existing explorer continues to calculate its result count from its loaded, filtered events. The nearby-radius behavior remains tracked separately in #87.

Follow-up local checks: TypeScript and 32 Node regression tests pass, including event API failure and empty-supply checks. Both Linux CI workflows passed on the initial PR head; the follow-up head must also pass before merge.

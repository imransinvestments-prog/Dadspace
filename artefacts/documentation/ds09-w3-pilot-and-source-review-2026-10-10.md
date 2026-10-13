# DS-09 updated pilot and source review

**11 October reconciliation:** Current decisions are 20 keep, 101 improve, 27 replace and 7 pause. Imran Tajuddin confirmed the 10 km radius and is the named content/technical owner. [Reconciliation summary](ds09-matrix-reconciliation-2026-10-11.md) supersedes the previous decision totals and provisional ownership/radius statements below. Earlier counts and checks remain historical evidence.

Owner update, 10 October 2026. This supersedes the earlier TW4 6AY pilot and unconfirmed age scope in the baseline report. Current centre: **W3 9LN**, Ealing; age scope: **0–5 inclusive**, including family programmes with evidence they suit children in that range. Postcodes.io coordinates: 51.508924, -0.275866. Radius remains the proposed 10 km straight-line working radius, not an agreed travel promise.

## Corrected interpretation of inactive sources

Inactive means the collector is not enabled; it does not mean the venue lacks worthwhile activities. The owner found useful programmes behind cookie consent on museum sites. A basic HTTP/insufficient-content result describes a fetch limitation, not supply. Treat wrong hosts, consent screens, JavaScript and missed detail links as access/discovery problems. Validate a supported rendered/detail route before deciding source usefulness. The owner's consent observations are recorded; this review verified official content through web retrieval, not an independent interactive replay of each consent flow.

### Aberdeen Museums: improve and retain as a national source

The earlier registry route used `www.aberdeencity.gov.uk`. The owner supplied the functioning [operator listing on sites.aberdeencity.gov.uk](https://sites.aberdeencity.gov.uk/AAGM/whats-aberdeen-art-galleries-and-museums). Verified linked pages:

- [Family fun: Loose parts play](https://sites.aberdeencity.gov.uk/AAGM/whats-aberdeen-art-galleries-and-museums/family-fun-loose-parts-play): ages 2–5 with an accompanying adult, named Wednesday sessions 10:30–12:30, free drop-in at the Art Gallery. Future dates include 4 November and 2 December 2026. Regular programme evidence supports Activities classification, despite the operator's Event labels.
- [Baby Boogie](https://sites.aberdeencity.gov.uk/AAGM/whats-aberdeen-art-galleries-and-museums/baby-boogie-8): listing specifies under-5s and adults; detail shows 7 November 2026 and 6 March 2027, 10:30–12:00 at Cowdray Hall, with paid booking. These two future occurrences alone do not establish a monthly schedule; retain dates and assess programme regularity/rarity from fuller evidence.

Recommendation changes **pause → improve**. Use the supplied host as a reviewed route candidate, follow family details and validate normal-worker extraction/repeat behavior. Aberdeen is outside W3 geography; its programmes provide useful national source evidence and under-5 category examples, not local pilot supply. No registry activation or live URL change was made.

### Amersham Museum: improve; useful wider-age coverage

[Museum Makers detail](https://amershammuseum.org/event/museum-makers-8/) explicitly states ages 7–11 and a session on 11 October 2026, 10:00–11:30. Tickets distinguish £12 first child and £8 second child. Its repeat-attendance offer indicates a programme with multiple sessions; exact recurrence must come from published sessions, not inference.

Retain **improve**, now with specific positive family-programme evidence. Museum Makers is outside the 0–5 pilot age range and outside the local pilot; that does not justify rejecting Amersham as a wider source. Its inactive flag and extraction/detail/repeat gaps remain operational issues rather than a relevance verdict.

Current recommendations after this review: **89 improve, 43 pause, 23 replace** across the same 155 source IDs. The [source table](ds09-source-decisions-2026-10-10.md), full matrix and builder now incorporate the recorded overrides. The original HTTP snapshot remains unchanged historical evidence; an official detail-page check does not prove the worker can ingest it. Neither source has been activated.

## Recomputed local inventory baseline

The [W3 radius snapshot](../data/ds09-w3-pilot-2026-10-10.json) stores coordinates, scope, exact read-only SQL and counts. It uses the same haversine method as the earlier audit and existing venue coordinates, not age suitability inferred from venue category.

| Category | Within 10 km | Public-visible | Linked stored activities |
|---|---:|---:|---:|
| Libraries | 105 | 103 | 0 |
| Museums | 115 | 115 | 0 |
| Children's playgrounds | 868 | 868 | 0 |
| Indoor/soft play | 11 | 11 | 0 |
| Trampolines | 2 | 2 | 0 |
| Zoo/animal parks | 5 | 5 | 0 |
| Amusement arcades | 9 | 9 | 0 |
| Uncategorised hidden candidates | 2 | 0 | 2 |

The two linked activities are Little Kickers records with age labels 18 months–8 years, attached to hidden uncategorised venue candidates. One lacks an event URL; neither is accepted pilot supply. Verify ages, individual class times, URLs and venue geocoding rather than assuming the whole 18-month–8-year range fits every session. Missing coordinates/unmatched activities remain outside the linked count; zero library/museum links is a collection/matching gap, not zero real programmes.

## Delivery requirements

Prioritise local Ealing/Acton libraries, museums and family centres, plus postcode-specific family providers; re-evaluate the depot versus central London museum distinction. The Hounslow observations remain useful historical evidence, not the new pilot's priority list.

Audit ages 0–5 without discarding family programmes that genuinely accommodate this range. Preserve older-age activities separately. Keep unknown suitability explicit and classify opportunities using the owner's regularity model rather than calendar/booking labels.

Under #39, investigate consent-state handling, the correct Aberdeen host, rendered fetch/detail discovery and unchanged-versus-empty-page behavior. A consent screen or blocked render must not produce accepted empty supply or renew verification timestamps. Existing robots, access, quality and release gates remain. Under #40, verify local venue identities/geocoding and preserve provenance. Under #70, expose inactive-versus-unsuitable, review evidence and consent/access failure states clearly to operators.

Validation: official listing/detail pages reviewed; radius SQL executed read-only; matrix builder reconciles all 155 source IDs. Owner is still Imran Tajuddin. #38 remains open for remaining per-source/access-policy review and technical maintenance ownership; pilot postcode and age range are now confirmed.

# Final three News location decisions

**Approved, applied and verified on 17 October 2026 at 15:44 UTC.** PR #184 deployed before the three-row transaction. Full 20-row readback and all ten public targeting cases pass. The proposal and application-gate wording below is retained as the reviewed before-state; no location decision remains on hold. See [Sprint 5 closure](./sprint-5-closure.md).

The 16 previously approved changes were committed and verified at 15:30 UTC on 17 October 2026. The following three rows are still unchanged, as instructed. These are revised, evidence-backed proposals for owner approval, not applied corrections.

| ID | Source evidence | Recommended targeting |
| --- | --- | --- |
| 736 | The syndicated Yahoo article was readable in the normal browser and explicitly locates the scheme at Boglestone Community Hub in Port Glasgow, funded by Inverclyde Council. | Scotland; local; district `inverclyde`, rather than `glasgow_city`. |
| 739 | The [publisher's full article](https://sandbach.nub.news/news/local-news/sp14219-wand-making-dodgeball-and-glow-stick-disco-your-guide-to-half-term-holiday-fun-310364) names multiple holiday-club venues across Cheshire, including Sandbach and Farndon. A single town/district would narrow the requested coverage incorrectly. | England; local county scope; `admin_area=cheshire`, no single locality. Requires the bounded county/filter fix below before application. |
| 855 | The [publisher's page](https://www.gazette-news.co.uk/news/26632520.bereaved-dad-praises-maldon-support-baby-loss-week/) was readable in the normal browser: its headline and body concern Maldon's community support. The publisher's name is Colchester Gazette, which does not establish the story's location. | England; local; `admin_area=essex`, `locality=maldon`, rather than Colchester or UK-wide. General emotional relevance is distinct from local targeting. |

For #736, [the publisher's area index](https://www.greenocktelegraph.co.uk/your-area/) lists the matching Port Glasgow headline; [reporting on the same scheme](https://www.glasgowview.com/inverclyde-launches-2-meals-and-winter-support-as-challenge-poverty-week-begins/) places the meals at Boglestone in Port Glasgow. The syndicated Yahoo body was subsequently verified through the normal browser and confirms the same location; earlier research-tool retrieval failures did not establish an inaccessible article.

## Bounded Cheshire filter repair

The existing geography contract had no `cheshire` county token. Simply writing that value would fail to reach users whose saved location identifies a constituent district. The prepared fix adds an explicit county reference and district context, preserves district-specific targeting and nation guards, and uses that context in postcode/API normalization. It does not change the schema or make local stories national. The county context covers Cheshire East, Cheshire West and Chester, Halton and Warrington; this is distinct from the newer Cheshire and Warrington combined authority. [Council ceremonial-area evidence](https://moderngov.cheshireeast.gov.uk/documents/s1438/Civic%20and%20Ceremonial%20Issues.pdf).

Regression checks cover county-wide delivery to each constituent district, no leakage of a district-only story to another district, no cross-nation leakage, and worker/API normalization parity. The News worker still ignores duplicate URL inserts, preserving reviewed geographic corrections on repeat ingestion. No paid model call or live ingestion is required for those checks.

## Apply gate

Approve or amend the three recommended mappings and the tested county-filter repair together. Deployment must precede the Cheshire data change. Application re-reads current rows, binds exact before snapshots, locks and updates only these three rows in one transaction, retains an inverse rollback plan, and verifies public readback plus intended-area filters. Previously applied IDs and the Monmouthshire no-op remain untouched. The two News tickets and Sprint 5 remain open until that gate and targeted acceptance are complete.

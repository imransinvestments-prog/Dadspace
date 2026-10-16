# Concise activity cards (#93)

## Remaining scope after #91

The dependency is released. Cards now share a consistent Schedule / Age guidance /
Price layout, reusing #91's interpreter with a compact presentation. The compact
view removes redundant generic recurrence when a pattern/date/period is already
shown and shortens only the future-session availability reminder. Unknown,
conflicting, past and ended warnings are preserved. No dates are generated.

Supplied age and cost text, including conditions, remains visible. Missing/blank
or explicit unknown cost becomes `Price unknown`; exact Free spelling is
normalised without turning trials, mixed free/paid conditions or absent prices
into free entry. All other supplied cost text is retained. No prices are filled.

Each card retains its detail link and adds Check source when a valid absolute
HTTP(S) listing/source link exists. Invalid/credential-bearing links are rejected;
valid source URL is the fallback. The same link validation and price wording is
used in details. Check source does not assert an aggregator is an official venue.

The card uses min-width protection, wrapping and labelled facts; raw long date
lists stay in detail. Detail and related summaries retain #91's full presentation.
No public eligibility, counts, queries, collectors, schema or production rows are
changed. Existing unrelated navigation/copy issues remain separately owned.

## Review and verification

- Rendered-card fixtures cover Free, paid/conditional, unknown, free trial,
  supplied age, long date lists, long URLs and absent/unsafe/fallback links.
- Retain #91 schedule/date/DST regressions and existing feed/radius/paging checks.
- Verify actual cards at 375px: price/source actions readable, no horizontal card
  overflow, no full raw date list; detail preserves original evidence.
- Read-only examples identified on 16 October: Archive Explorers Club (Free,
  under 5s, explicit dates), Mum & Baby Pilates with Lottie (£15 per class,
  8 weeks to 12 months, source-page fallback), and Henley Rhymetime (missing
  price, long date list retained in detail). These are examples, not new factual
  approvals or a frozen nationwide price audit. The rendered adversarial fixtures
  are clearly test data and do not publish new records.
- Owner preview approval then release and production verification precede closure.
  Rollback is reverting the application patch; no database rollback is needed.

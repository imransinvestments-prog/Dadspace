# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

A responsive Next.js site, installable as a PWA ("Add Dadspace to your home screen"). Most use is mobile web; the desktop layout adds a sidebar. There is no native app.

## Users

All UK parents and carers: dads, mums, grandparents and anyone else looking after children. The product speaks in a dad's voice, but the audience is not limited to dads.

The typical situation is a parent on a phone, often outdoors or with a child in tow, working out what to do with the kids nearby: this weekend, this afternoon, or on a regular weekday slot.

Data coverage currently centres on the W3 9LN pilot (10 km radius, children aged 0–5; see `docs/discovery-model.md`). National and wider-age listings are kept and shown because they are still useful. The pilot is a coverage starting point, not the audience boundary.

## Product Purpose

Dadspace helps families find things to do and stay on top of family life in one place:

- **Places** (venues): playgrounds, parks, museums, libraries, soft play, family centres and more. A venue is useful on its own, whether or not any activities or events are known there.
- **Activities**: regular opportunities such as storytimes, rhyme times and classes.
- **Events**: infrequent or one-off occasions.
- **News**: family and local news, with a "why it matters" summary.
- **Ideas** (Originals): daily tips and weekend guides.
- **Deals**: offers on baby and kids' kit.

Success means a parent quickly finds something suitable nearby and gets there (directions, phone, website), and comes back for the weekly rhythm of planning.

## Positioning

- **Hyper-local:** results come nearest first from the visitor's location or a searched town or postcode, with approximate straight-line distances and local news.
- **Everything in one place:** days out, regular activities, rare events, news and kit deals together, instead of four separate sites.
- **A dad's voice:** warm, practical and lightly funny (dad jokes, "2 sleeps till the weekend"), written by and for dads but welcoming to every parent and carer.
- **Basic validation, not vetting:** listings pass basic checks (licensed and credited photos, classification from evidence of regularity, gaps admitted openly). Dadspace must not claim that listings are vetted, inspected, verified or endorsed.

## Operating Context

- Listings are collected by Python workers and source adapters into Supabase, classified under the discovery model (venues are places, activities are regular, events are rare) and published after owner review through the `/ops` review desk.
- Imran Tajuddin is the accountable owner for content review and technical upkeep. Production data changes, source activation or pausing, terms reviews and venue fact labels are owner decisions.
- Delivery runs in sprints tracked in GitHub issues. Each change ships as its own PR after CI and the Vercel preview pass.

## Capabilities and Constraints

- Location comes from the device or a UK town/postcode search; distances are approximate straight-line distances.
- Venue photos come from Wikimedia Commons (CC-licensed, with attribution) or Google Places (with author credit). When neither is available, a category illustration is shown and labelled as not a photo of the venue. Proxying or caching these photos raises terms questions the owner must decide.
- Missing facts are stated, not guessed (for example "Access information not supplied. Check with the venue before visiting.").
- Accounts use Supabase auth (email/password and Google). The forum is built but switched off until community features and moderation are accepted (`FORUM_ENABLED = false`).
- `COMING_SOON` in `lib/launch.ts` is a maintenance hold only. Public launch was 8 October 2026.

## Brand Commitments

- Name: **Dadspace**, written as the lowercase logotype "dad**space**" with "space" in the brand orange. App icon: `public/icon-512.png`.
- Tagline in use: "Made for UK dads". Voice: plain British English, friendly, practical and lightly humorous; dad jokes are part of the product (home "Dad joke break").
- Locale: en-GB.

## Evidence on Hand

- Real listings: UK venues, regular activities and events from the collectors, with the provenance recorded in `docs/`.
- Category illustrations and hero imagery in `public/images/`. These are illustrations, not photos of real venues, and are labelled as such.
- No testimonials, user numbers, press coverage or partnerships exist. Do not invent them.

## Product Principles

1. **Useful nearby, fast.** Nearest-first discovery and one-tap actions (directions, call, website) come before browsing depth.
2. **Honest about what we know.** State gaps, label illustrations, credit photos, and never upgrade basic validation into a quality or safety claim.
3. **Places stand on their own.** A venue earns its listing without events; a useful listing survives an unresolved venue match.
4. **One dad-voiced home for family life.** Discovery, news, ideas and deals share one tone and one way of working, inclusive of every parent and carer.

## Accessibility & Inclusion

- Target: WCAG 2.2 AA, best effort. Aim for AA in all new work and fix regressions, but AA gaps do not automatically block a release.
- Use is mostly on phones, often outdoors, so text contrast and 44px touch targets matter in practice.
- Language must include all parents and carers, not only dads.

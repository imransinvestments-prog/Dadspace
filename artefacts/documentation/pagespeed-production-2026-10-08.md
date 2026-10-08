# Dadspace production PageSpeed checks

Measured 8 October 2026, 14:02–14:20 BST, production commit `693edc92867105ed36953764225348aa6746074f`. Three initial-load lab runs per route and device. Lighthouse 13.5.0; mobile Moto G Power, slow 4G; desktop custom throttling. Each report contains mobile and desktop tabs. PR #55 subsequently added a hidden results heading and category-matched share artwork; final deployment `a9ca6d7cfbb73fa428ad83622ee54edc022a9f8e` passed HTTP checks.

No CrUX field data is available. These measurements do not establish INP or field p75 Core Web Vitals. Earlier production baseline attempts failed (domain resolution and API quota), so no before/after improvement percentage is claimed.

| Route | Mobile performance | Desktop performance | Mobile LCP | Mobile TBT | Mobile CLS |
|---|---:|---:|---:|---:|---:|
| [/](https://www.dad-space.co.uk/) | 94 | 99 | 3s | 30ms | 0.001 |
| [/venues](https://www.dad-space.co.uk/venues) | 97 | 100 | 2.6s | 10ms | 0.001 |
| [/places/hounslow/libraries](https://www.dad-space.co.uk/places/hounslow/libraries) | 95 | 100 | 2.9s | 60ms | 0.001 |
| [/venues/hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a](https://www.dad-space.co.uk/venues/hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a) | 97 | 100 | 2.6s | 40ms | 0.003 |

## Exact runs

Scores and metrics below are displayed lab values. The columns are performance / LCP seconds / TBT milliseconds / CLS.

| Route | Report | Mobile | Desktop |
|---|---|---|---|
| / | [Run 1](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk/8a1brp7y26?form_factor=mobile) | 94 / 3 / 30 / 0.001 | 89 / 0.6 / 0 / 0.079 |
| / | [Run 2](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk/iesxw4dyvw?form_factor=mobile) | 94 / 3 / 0 / 0.001 | 100 / 0.5 / 0 / 0.016 |
| / | [Run 3](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk/jyo59lbkyf?form_factor=mobile) | 92 / 3.3 / 80 / 0 | 99 / 0.6 / 20 / 0.016 |
| /venues | [Run 1](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-venues/9xagdyw7lf?form_factor=mobile) | 99 / 2.1 / 60 / 0 | 100 / 0.6 / 0 / 0.016 |
| /venues | [Run 2](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-venues/rov20vf8al?form_factor=mobile) | 96 / 2.7 / 10 / 0.001 | 100 / 0.5 / 10 / 0.016 |
| /venues | [Run 3](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-venues/uiwszcmudy?form_factor=mobile) | 97 / 2.6 / 0 / 0.001 | 99 / 0.6 / 0 / 0.016 |
| /places/hounslow/libraries | [Run 1](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-places-hounslow-libraries/xthxos47ae?form_factor=mobile) | 89 / 3.6 / 10 / 0 | 100 / 0.5 / 10 / 0.016 |
| /places/hounslow/libraries | [Run 2](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-places-hounslow-libraries/j26xhe83q7?form_factor=mobile) | 95 / 2.9 / 60 / 0.001 | 100 / 0.5 / 0 / 0.016 |
| /places/hounslow/libraries | [Run 3](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-places-hounslow-libraries/avsnqtnfx0?form_factor=mobile) | 98 / 2.4 / 60 / 0.001 | 100 / 0.6 / 20 / 0.016 |
| /venues/hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a | [Run 1](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-venues-hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a/qbhkhpuo3m?form_factor=mobile) | 97 / 2.6 / 10 / 0.003 | 100 / 0.5 / 40 / 0.017 |
| /venues/hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a | [Run 2](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-venues-hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a/6iw68lztw3?form_factor=mobile) | 96 / 2.6 / 100 / 0.003 | 100 / 0.5 / 20 / 0.017 |
| /venues/hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a | [Run 3](https://pagespeed.web.dev/analysis/https-www-dad-space-co-uk-venues-hounslow-library--44edbcfa-3c4b-42dc-82ba-fd973dab751a/o8nobz0nu0?form_factor=mobile) | 97 / 2.7 / 40 / 0.003 | 100 / 0.6 / 0 / 0.017 |

## Verification and remaining work

- Public HTML, internal links, canonicals, hidden-venue 404, renamed-slug 308, bounded API reads and page-2 ordering passed. All 16 venue sitemap shards contained 58,500 unique public URLs; core sitemap contained 644 URLs.
- At 390px/DPR 1, the 128px tile selected a 256px WebP (12,152 bytes). Actual DPR 2/3 selection remains unmeasured; returned 384/640 variants are candidates, not device evidence.
- [Google Rich Results Test](https://search.google.com/test/rich-results/result?id=u_pw-dpYMDA8LVGFgPAL8w) crawled the live Hounslow Library detail successfully and found three valid items: breadcrumbs, local business and organisation. Optional missing telephone/priceRange/image fields remain unknown rather than invented.
- Search Console reports no access to a verified dad-space.co.uk property in the available account. Property owner access is required for indexing and sitemap-submission evidence.
- Mobile lab LCP remains above 2.5 seconds in the medians. The sampled slow category LCP element was introductory text with render delay; adding image priority is not justified for that result. Remaining diagnostics include unused JavaScript, image delivery and brand-text contrast.
- Public eligibility retains the existing visibility policy. The 55,568 historical `existing` records have not received a new human review in this release; #33/#34 retain publication/quality ownership. News accuracy and editorial approval remain #35.

[Ticket #53](https://github.com/imransinvestments-prog/Dadspace/issues/53) tracks outstanding acceptance; [PR #54](https://github.com/imransinvestments-prog/Dadspace/pull/54) and [PR #55](https://github.com/imransinvestments-prog/Dadspace/pull/55) are merged.


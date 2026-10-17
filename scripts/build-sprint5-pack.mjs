// Offline only. Captured SQL and capture timestamps live beside each input.
import fs from 'node:fs'
import { createHash } from 'node:crypto'
import { selectDeals } from '../lib/deals-selection.ts'
const read = name => JSON.parse(fs.readFileSync(`artefacts/data/sprint5-${name}-baseline.json`, 'utf8'))
const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex')
const rows = (items, title) => items.map(row => ({ id: String(row.id), title: String(row[title]), fields: row }))
const summary = (items, field) => Object.fromEntries([...new Set(items.map(r => String(r[field] ?? 'unknown')))].sort().map(value => [value, items.filter(r => String(r[field] ?? 'unknown') === value).length]))
const venues = read('venues'), activities = read('activities'), deals = read('deals')
const selected = selectDeals(deals.rows, 1000, Date.parse(deals.captured_at))
const packs = {
  venues: { captured_at: venues.captured_at, pool_count: venues.pool_count, method: 'Published, unmerged venues within 10km of W3 9LN; category round-robin then md5(id), limit 50. Age suitability is not inferred.', rows: rows(venues.rows, 'venue_name') },
  activities: { captured_at: activities.captured_at, pool_count: activities.pool_count, method: 'Current activity view, linked pilot-area rows first, then category/source round-robin and md5(id), limit 100. National diagnostic cohort; unknown distance/age is not pilot eligibility.', rows: rows(activities.rows, 'title') },
  deals: { captured_at: deals.captured_at, pool_count: selected.length, stored_count: deals.stored_count, live_status_count: deals.live_status_count, candidate_count: deals.rows.length, method: 'Exact shared selectDeals at captured_at over all fresh live active-taxonomy quality candidates. All selected published offers, not stored variants. Top subset is first min(20,N).', rows: rows(selected.map((r, i) => ({ ...r, rank: i + 1 })), 'title') },
}
for (const pack of Object.values(packs)) {
  pack.fingerprints = Object.fromEntries(pack.rows.map(row => [row.id, hash(row)]))
  pack.manifest_sha256 = hash(pack.rows)
  pack.human_labels = 'Not supplied. Automated fields and unknowns are not owner scores.'
}
packs.activities.coverage = { category: summary(activities.rows, 'category'), source: summary(activities.rows, 'source_name'), linked_within_10km: activities.rows.filter(r => r.distance_km != null && r.distance_km <= 10).length, unknown_distance: activities.rows.filter(r => r.distance_km == null).length, unknown_age: activities.rows.filter(r => !r.age_range).length }
packs.venues.coverage = { category: summary(venues.rows, 'category') }
packs.deals.coverage = { retailer: summary(selected, 'retailer'), group: summary(selected, 'display_group') }
fs.writeFileSync('artefacts/data/sprint5-review-pack.json', JSON.stringify(packs, null, 2) + '\n')
console.log(JSON.stringify(Object.fromEntries(Object.entries(packs).map(([key,pack]) => [key, { rows: pack.rows.length, pool: pack.pool_count, coverage: pack.coverage }]))))

import fs from "node:fs"
import { selectDeals } from "../lib/deals-selection.ts"
const root = new URL("../", import.meta.url)
const read = path => JSON.parse(fs.readFileSync(new URL(path, root), "utf8"))
const baseline = read("artefacts/data/sprint7-deals-baseline.json")
const candidates = read("artefacts/data/sprint7-deals-candidates.json")
// Freeze evaluation time to the snapshot. A later replay must not silently alter the baseline.
const observed = Math.max(...[...baseline.sources.map(s => s.last_checked_at), ...candidates.map(d => d.last_seen)].map(v => Date.parse(v || "")).filter(Number.isFinite))
const displayed = selectDeals(candidates, 100, observed)
const priorityIds = new Set([74,75,76,77,78,155,156,157,158,159,160,161,162,163,164,215,216,217,218,219,220,221,222,255,256,454,455,910,913,919,920,921,922,923,924,925,926,927,932])
const priority = t => priorityIds.has(t.id)
const sources = new Map(baseline.sources.map(s => [s.id, s]))
const rows = baseline.taxonomy.filter(t => t.active || priority(t)).map(t => {
  const yields = baseline.yield.filter(y => y.item_id === t.id)
  const routes = yields.map(y => sources.get(y.source_id)).filter(Boolean)
  return { id: t.id, item: t.item_or_service, active: t.active, group: t.display_group, terms: t.uk_terms, equivalentItem: t.equivalent_item_id,
    priorityCandidate: priority(t), displayed: displayed.filter(d => d.item_id === t.id).length,
    historicalSources: [...new Set(routes.map(s => s.id + ": " + s.name))],
    gap: routes.length ? "Historical stored route exists; current useful yield and offer evidence still need qualification" : "No item-level collected route evidenced in this snapshot; source qualification gap",
    configuredCandidateSources: [74,75,76,77,78,910,932].includes(t.id) ? [1] : t.subcategory === "School Uniform" ? [28] : [454,455].includes(t.id) ? [27,34] : [],
    inactiveReason: t.inactive_reason }
})
const result = { observedAt: new Date(observed).toISOString(), activeItems: baseline.taxonomy.filter(t => t.active).length,
  mappedRows: rows.length, displayedIds: displayed.map(d => d.id), displayedCount: displayed.length,
  groups: [...new Set(displayed.map(d => d.display_group))], rows,
  caution: "Snapshot selector replay is not new owner acceptance. Historical stored routes and configured candidate feeds do not prove current coverage. Accessory mappings must not substitute for car-seat or bicycle offers." }
fs.writeFileSync(new URL("artefacts/data/sprint7-deals-coverage.json", root), JSON.stringify(result, null, 2) + "\n")
console.log(JSON.stringify({observedAt: result.observedAt, activeItems: result.activeItems, mappedRows: rows.length, displayedCount: displayed.length, groups: result.groups, priority: rows.filter(r => r.priorityCandidate).map(({id,item,displayed,historicalSources}) => ({id,item,displayed,historicalSources}))}, null, 2))

import type { Article } from "./types"
export function selectNewsCards(rows: Article[], count = 8): Article[] {
  // Homepage is a small curated surface: prefer strong family relevance over category quotas.
  rows = rows.filter(row => (row.relevance ?? 0) >= 4).sort((a,b) => (b.relevance ?? 0) - (a.relevance ?? 0) || String(b.published_at ?? "").localeCompare(String(a.published_at ?? "")))
  const chosen: Article[] = [], categories = new Set<string>(), ids = new Set<string>()
  for (const row of rows) {
    if (ids.has(row.id) || categories.has(row.category ?? "other")) continue
    chosen.push(row); ids.add(row.id); categories.add(row.category ?? "other")
    if (chosen.length === count) return chosen
  }
  for (const row of rows) {
    if (ids.has(row.id)) continue
    chosen.push(row); ids.add(row.id)
    if (chosen.length === count) break
  }
  return chosen
}
export function activeThisWeek(row: {start_date: string | null; end_date: string | null; recurrence: string | null}, start: string, end: string) {
  if (row.start_date && row.start_date > end) return false
  if (row.end_date) return row.end_date >= start
  if (row.recurrence === "recurring") return true
  return Boolean(row.start_date && row.start_date >= start)
}

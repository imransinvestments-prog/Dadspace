export type SourceEvidence = {
  id: string | number; name: string; active: boolean; family: "Discovery" | "Deals" | "News"
  role: string | null; nation: string | null; region: string | null
  checked: string | null; succeeded: string | null; failures: number
  yield: number | null; yieldLabel: string; failed: boolean
}

export function sourceSignals(source: SourceEvidence, now = new Date()) {
  const checked = source.checked ? Date.parse(source.checked) : NaN
  const stale = !Number.isFinite(checked) || checked > now.getTime() || now.getTime() - checked > 36 * 60 * 60 * 1000
  return {
    collection: !source.active ? "Inactive" : source.failed || source.failures > 0 ? "Failure recorded" :
      !Number.isFinite(checked) ? "Not observed" : "No failure recorded",
    freshness: !Number.isFinite(checked) ? "Not observed" : stale ? "Check overdue" : "Checked within 36h",
    yield: source.yield === null ? "Unknown" : source.yield === 0 ? "Zero observed yield" : `${source.yield} ${source.yieldLabel}`,
    attention: source.active && (stale || source.failed || source.failures > 0 || source.yield === 0),
  }
}

export type QueueKind = "venues" | "activities" | "events"
export const PAGE_SIZE = 20
export function reviewQuery(kind?: string | string[], page?: string | string[]) {
  const selected: QueueKind = kind === "activities" || kind === "events" ? kind : "venues"
  const number = typeof page === "string" && /^[1-9]\d{0,3}$/.test(page) ? Number(page) : 1
  return { kind: selected, page: number }
}

// Links are evidence only; never render executable schemes or embedded credentials.
export function evidenceUrl(value: unknown): string | null {
  if (typeof value !== "string") return null
  try {
    const url = new URL(value)
    if (!["https:", "http:"].includes(url.protocol) || url.username || url.password) return null
    // Keep public record identities (e.g. MyLibrary ?id=...), remove signed tokens.
    const identities = [...url.searchParams.entries()].filter(([key, value]) =>
      (["id", "eventid", "variant", "page"].includes(key.toLowerCase()) && /^[a-zA-Z0-9_-]{1,100}$/.test(value)) ||
      (url.hostname === "www.matalan.co.uk" && key === "variation" && /^\d{1,12}$/.test(value)))
    url.search = ""
    for (const [key, value] of identities) url.searchParams.append(key, value)
    url.hash = ""
    return url.toString()
  } catch { return null }
}

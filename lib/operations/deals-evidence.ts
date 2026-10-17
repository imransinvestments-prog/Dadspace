import "server-only"
import { getSupabase } from "@/lib/supabase"
import { getDeals } from "@/lib/deals"
import { operationsAccess } from "./session"
import { evidenceUrl } from "./evidence-shared"
import trial from "@/artefacts/data/sprint7-new-offers.json"
import { dealDisplayTitle } from "@/lib/deals-selection"

export type DealEvidenceRow = { id: string; title: string; state: string; detail: string; url: string | null; source: string; date: string | null }
function collectionCounts(value: unknown) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return "Collection yield unknown."
  const counts = value as Record<string, unknown>
  const count = (v: unknown) => typeof v === "number" && Number.isFinite(v) && v >= 0 ? String(v) : "unknown"
  const rejected = counts.rejected && typeof counts.rejected === "object" && !Array.isArray(counts.rejected) ? Object.entries(counts.rejected).slice(0, 25).map(([reason, n]) => `${reason.replaceAll("_", " ").slice(0, 200)}: ${count(n)}`).join("; ") : "unknown"
  return `Fetched: ${count(counts.fetched)}. Verified offers: ${count(counts.verified)}. Rejection reasons: ${rejected || "none recorded"}.`
}
export async function getDealsEvidence(kind: string, page: number, filter: string) {
  const access = await operationsAccess()
  const unavailable = { available: false, total: null as number | null, rows: [] as DealEvidenceRow[] }
  if (access !== "allowed") return { access, evidence: unavailable }
  const db = getSupabase()
  if (!db) return { access, evidence: unavailable }
  const from = (page - 1) * 20
  try {
    let rows: DealEvidenceRow[] = [], total: number | null = null
    if (kind === "trial") {
      rows = trial.rows.slice(from, from + 20).map(r => ({ id: r.id, title: dealDisplayTitle(r.title), state: trial.ownerAccepted ? "Owner-approved offer snapshot — collection/publication verified separately" : "Candidate only — not published or owner-approved", source: "Natural Baby Shower · canonical item " + r.itemId, url: evidenceUrl(r.link), date: trial.checkedOn,
        detail: `Trial price: £${r.price}; merchant comparison: £${r.comparison}. ${r.description} Independently rechecked exact variant using the existing merchant-advertised policy. This is a dated snapshot: stock/prices must be rechecked before activation/publication. No car-seat fitting or compatibility recommendation is implied. Snapshot SHA-256: ${r.fingerprint}` }))
      total = trial.rows.length
    } else if (kind === "taxonomy") {
      let query = db.from("parent_discount_items").select("id,item_or_service,active,inactive_reason,display_group,uk_terms,deal_type,equivalent_item_id,needs_child_evidence", { count: "exact" })
      if (filter === "active") query = query.eq("active", true)
      if (filter === "inactive") query = query.eq("active", false)
      if (filter === "aliases") query = query.not("equivalent_item_id", "is", null)
      const result = await query.order("id").range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      if (result.error || !result.data || result.count === null) return { access, evidence: unavailable }
      // The exact public selector supplies current displayed coverage, not stored/live counters.
      const published = await getDeals()
      rows = result.data.map(r => ({ id: String(r.id), title: r.item_or_service, state: r.active ? "Active canonical item" : "Inactive canonical item", source: r.display_group || "No public group", url: null, date: null,
        detail: `Terms: ${r.uk_terms || "unknown"}. Type: ${r.deal_type || "unknown"}. Equivalent item: ${r.equivalent_item_id ?? "none recorded"}. Child evidence: ${r.needs_child_evidence ? "required" : "not separately required"}. ${r.inactive_reason ? "Inactive reason: " + r.inactive_reason + ". " : ""}Displayed offers: ${published.loadFailed ? "unavailable" : published.items.filter(d => d.item_id === r.id).length}. Zero displayed offers is a coverage gap, not proof of no source supply.` }))
      total = result.count
    } else if (kind === "sources") {
      let query = db.from("deal_sources").select("id,name,url,source_type,active,last_status,last_checked_at,last_success_at,consecutive_failures,last_counts", { count: "exact" })
      if (filter === "active") query = query.eq("active", true)
      if (filter === "inactive") query = query.eq("active", false)
      const result = await query.order("id").range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      if (result.error || !result.data || result.count === null) return { access, evidence: unavailable }
      rows = result.data.map(r => ({ id: String(r.id), title: r.name, state: r.active ? "Active" : "Inactive", source: r.source_type, url: evidenceUrl(r.url), date: r.last_checked_at,
        detail: `Last status: ${r.last_status ?? "unknown"}; last successful fetch: ${r.last_success_at ?? "unknown"}; consecutive failures: ${r.consecutive_failures ?? "unknown"}. ${collectionCounts(r.last_counts)} A successful fetch does not prove useful offers. Affiliate membership/terms are not established by source activation.` }))
      total = result.count
    } else if (kind === "audit") {
      const result = await db.from("operations_maintenance_audit").select("id,action,record_id,reason,created_at,status,reverted_by", { count: "exact" }).eq("family", "deals-source").order("created_at", { ascending: false }).order("id").range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      if (result.error || !result.data || result.count === null) return { access, evidence: unavailable }
      rows = result.data.map(r => ({ id: r.id, title: `${r.action} · source ${r.record_id}`, state: r.status, source: "Deals source maintenance", url: null, date: r.created_at, detail: `${r.reason}${r.reverted_by ? " · Restored by audit " + r.reverted_by : ""}` }))
      total = result.count
    } else {
      const published = await getDeals()
      if (filter === "displayed" && published.loadFailed) return { access, evidence: unavailable }
      if (filter === "displayed" && published.items.length === 0) return { access, evidence: { available: true, total: 0, rows: [] } }
      let query = db.from("deals").select("id,title,status,retailer,link,source_id,item_id,last_seen,expires_at,price,was_price,discount_pct,audience_evidence,classified_by,description", { count: "exact" })
      if (filter === "live") query = query.eq("status", "live")
      if (filter === "displayed") query = query.in("id", published.items.map(r => r.id))
      const result = await query.order("id", { ascending: false }).range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      if (result.error || !result.data || result.count === null) return { access, evidence: unavailable }
      const displayed = new Set(published.items.map(r => String(r.id)))
      rows = result.data.map(r => ({ id: String(r.id), title: r.title, source: `${r.retailer || "Unknown merchant"} · source ${r.source_id ?? "unknown"} · item ${r.item_id ?? "unmapped"}`, url: evidenceUrl(r.link), date: r.last_seen,
        state: published.loadFailed ? "Public status unavailable" : displayed.has(String(r.id)) ? "Displayed by the public selector" : "Stored — outside the current public selection",
        detail: `Stored status: ${r.status}. Price: ${r.price ?? "unknown"}; comparison: ${r.was_price ?? "unknown"}; discount: ${r.discount_pct ?? "unknown"}%. Expiry: ${r.expires_at ?? "not recorded"}. Evidence: ${r.classified_by || "unknown"}. Audience: ${r.audience_evidence || "unknown"}. ${String(r.description || "").slice(0, 2500)} Stock is supported only by the last verification; recheck the merchant before purchase. Merchant comparison prices are not independent price history.` }))
      total = result.count
    }
    return { access, evidence: { available: true, total, rows } }
  } catch { return { access, evidence: unavailable } }
}

import "server-only"
import { getSupabase } from "@/lib/supabase"
import { operationsAccess } from "./session"
import { evidenceUrl } from "./evidence-shared"

export type EditorialRow = { id: string; title: string; state: string; source: string | null; url: string | null; date: string | null; detail: string | null; draft: string | null }
type Evidence = { available: boolean; total: number | null; rows: EditorialRow[] }
const unavailable: Evidence = { available: false, total: null, rows: [] }
const text = (v: unknown, max = 300) => typeof v === "string" ? v.slice(0, max) : null
function draftText(v: unknown) {
  if (!v || typeof v !== "object" || Array.isArray(v)) return null
  const d = v as Record<string, unknown>
  const parts = [text(d.title), text(d.summary, 1000)]
  if (Array.isArray(d.sections)) for (const s of d.sections.slice(0, 7)) {
    if (s && typeof s === "object") {
      parts.push(text(s.heading))
      if (Array.isArray(s.paragraphs)) for (const p of s.paragraphs.slice(0, 4)) parts.push(text(p, 1800))
    }
  }
  return parts.filter(Boolean).join("\n\n").slice(0, 20000)
}
export async function getEditorialEvidence(kind: string, page: number, filter = "all") {
  const access = await operationsAccess()
  if (access !== "allowed") return { access, evidence: unavailable }
  const db = getSupabase()
  if (!db || !process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY) return { access, evidence: unavailable }
  const from = (page - 1) * 20
  try {
    let evidence: Evidence = unavailable
    if (kind === "news") {
      let query = db.from("news_items").select("id,title,url,source_name,published_at,relevance,is_primary,ops_hidden", { count: "exact" })
      if (filter === "hidden") query = query.eq("ops_hidden", true)
      if (filter === "duplicates") query = query.eq("is_primary", false)
      if (filter === "low-relevance") query = query.lt("relevance", 3)
      if (filter === "missing-link") query = query.or("url.is.null,url.eq.")
      const { data, error, count } = await query.order("id", { ascending: false }).range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      if (!error && data && count !== null) {
        const publicRows = data.length ? await db.from("feed_items").select("id").in("id", data.map(r => r.id)).abortSignal(AbortSignal.timeout(10_000)) : { data: [], error: null }
        const publicIds = publicRows.error || !publicRows.data ? null : new Set(publicRows.data.map(r => String(r.id)))
        evidence = { available: true, total: count, rows: data.map(r => ({ id: String(r.id), title: r.title, source: r.source_name, url: evidenceUrl(r.url), date: r.published_at, state: r.ops_hidden ? "Hidden by operator" : !publicIds ? "Public status unavailable" : publicIds.has(String(r.id)) ? "Published in the News feed" : "Stored — outside the current public feed", detail: `Relevance: ${r.relevance ?? "unknown"}; primary: ${r.is_primary ?? "unknown"}. Feed eligibility depends on publication date, relevance and duplicate rules.`, draft: null })) }
      }
    } else if (kind === "originals") {
      let query = db.from("original_posts").select("slug,title,cadence,published_at,ops_hidden,sections,summary", { count: "exact" })
      if (filter === "hidden") query = query.eq("ops_hidden", true)
      const { data, error, count } = await query.order("published_at", { ascending: false }).order("slug").range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      if (!error && data && count !== null) evidence = { available: true, total: count, rows: data.map(r => ({ id: r.slug, title: r.title, source: "Dadspace Originals", url: null, date: r.published_at, state: r.ops_hidden ? "Hidden by operator" : "Published", detail: r.cadence, draft: draftText(r) })) }
    } else if (kind === "drafts") {
      let query = db.from("original_content_attempts").select("id,run_id,cadence,slot_date,created_at,stage,attempt,draft,detail,model_calls,input_tokens,output_tokens,dry_run", { count: "exact" })
      if (filter === "rejected") query = query.in("stage", ["validation_rejected", "editor_rejected"])
      if (filter === "failed") query = query.eq("stage", "failed")
      const { data, error, count } = await query.order("created_at", { ascending: false }).order("id").range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      const stageLabels: Record<string, string> = { draft: "Draft retained", validation_rejected: "Validation rejected draft", editor_rejected: "AI editor rejected draft", approved: "AI editorial check passed — not owner acceptance", published: "Publication confirmed", duplicate: "Duplicate slot skipped", failed: "Failure recorded — inspect run", dry_run: "Dry-run check — no publication" }
      if (!error && data && count !== null) evidence = { available: true, total: count, rows: data.map(r => ({ id: r.id, title: `${r.cadence} ${r.slot_date} — attempt ${r.attempt}`, source: r.run_id ? `Workflow run ${r.run_id}` : "Run not recorded", url: /^\d+$/.test(r.run_id || "") ? `https://github.com/imransinvestments-prog/Dadspace/actions/runs/${r.run_id}` : null, date: r.created_at, state: stageLabels[r.stage] || "Unknown stage", detail: `${r.dry_run ? "Dry run (model calls may cost money)" : "Live mode"}. ${text(r.detail, 1500)}. Cumulative requests for this slot run: ${r.model_calls ?? "unknown"}; ${r.input_tokens ?? "unknown"} input / ${r.output_tokens ?? "unknown"} output tokens. Billed cost unknown.`, draft: draftText(r.draft) })) }
    } else if (kind === "sources") {
      const { data, error, count } = await db.from("news_sources").select("id,name,feed_url,active,last_checked_at,consecutive_failures,last_error", { count: "exact" }).order("id").range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      if (!error && data && count !== null) evidence = { available: true, total: count, rows: data.map(r => ({ id: String(r.id), title: r.name, source: "News feed", url: evidenceUrl(r.feed_url), date: r.last_checked_at, state: r.active ? "Active" : "Inactive", detail: `${r.consecutive_failures ?? "unknown"} consecutive failures. ${r.last_error ? "A source error is recorded; inspect the workflow." : "No error currently recorded; this does not prove useful yield."}`, draft: null })) }
    } else if (kind === "audit") {
      const { data, error, count } = await db.from("operations_maintenance_audit").select("id,actor_id,action,family,record_id,reason,created_at,status,run_id,reverted_by", { count: "exact" }).order("created_at", { ascending: false }).order("id").range(from, from + 19).abortSignal(AbortSignal.timeout(10_000))
      if (!error && data && count !== null) evidence = { available: true, total: count, rows: data.map(r => ({ id: r.id, title: `${r.action} · ${r.family} · ${r.record_id}`, source: `Actor ${r.actor_id}`, url: r.run_id ? `https://github.com/imransinvestments-prog/Dadspace/actions/runs/${r.run_id}` : null, date: r.created_at, state: r.status, detail: `${text(r.reason, 1000)}${r.reverted_by ? ` · Restored by ${r.reverted_by}` : ""}`, draft: null })) }
    }
    return { access, evidence }
  } catch { return { access, evidence: unavailable } }
}

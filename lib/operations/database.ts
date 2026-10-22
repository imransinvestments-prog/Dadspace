import "server-only"
import { getSupabase } from "@/lib/supabase"
import { operationsAccess } from "./session"
import { PAGE_SIZE, reviewQuery, type SourceEvidence } from "./evidence-shared"
import type { SupabaseClient } from "@supabase/supabase-js"

type ReadResult<T> = { available: true; value: T } | { available: false }
type Row = Record<string, unknown>
type Response = { error: unknown; data: unknown; count: number | null }
const unavailable = { available: false } as const
const text = (value: unknown) => typeof value === "string" ? value : null
const count = (value: unknown) => typeof value === "number" && Number.isSafeInteger(value) && value >= 0 ? value : null
function client() {
  // The shared public client can fall back to anon. Empty RLS reads are not evidence.
  try { return process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY ? getSupabase() : null }
  catch { return null }
}
async function read<T>(query: PromiseLike<Response>, convert: (data: Response) => T): Promise<ReadResult<T>> {
  try { const result = await query; if (result.error) return unavailable; return { available: true, value: convert(result) } }
  catch { return unavailable }
}
function rows(result: Response, bounded = false): Row[] {
  if (!Array.isArray(result.data) || result.data.some(row => !row || typeof row !== "object" || Array.isArray(row))) throw new Error("Invalid evidence")
  if (bounded && (count(result.count) === null || result.count! > result.data.length)) throw new Error("Incomplete evidence")
  return result.data as Row[]
}
function total(result: Response) {
  const value = count(result.count)
  if (value === null) throw new Error("Missing total")
  return value
}
async function sourceRows(db: SupabaseClient, family: SourceEvidence["family"]): Promise<ReadResult<SourceEvidence[]>> {
  const table = family === "Discovery" ? "sources" : family === "Deals" ? "deal_sources" : "news_sources"
  const projection = family === "Discovery" ? "id,name,active,source_role,nation,region,last_checked_at,last_success_at,fail_count,last_event_count" :
    family === "Deals" ? "id,name,active,last_status,last_checked_at,last_success_at,consecutive_failures,last_counts" :
      "id,name,active,last_checked_at,consecutive_failures,last_error"
  return read(db.from(table).select(projection, { count: "exact" }).order("id").range(0, 499).abortSignal(AbortSignal.timeout(10_000)), result => rows(result, true).map(row => {
    if ((typeof row.id !== "string" && typeof row.id !== "number") || typeof row.name !== "string" || typeof row.active !== "boolean") throw new Error("Invalid source")
    const dealCounts = row.last_counts && typeof row.last_counts === "object" ? row.last_counts as Row : {}
    return { id: row.id, name: row.name, active: row.active, family, role: text(row.source_role), nation: text(row.nation), region: text(row.region),
      checked: text(row.last_checked_at), succeeded: text(row.last_success_at), failures: count(row.fail_count ?? row.consecutive_failures) ?? 0,
      yield: family === "Discovery" ? count(row.last_event_count) : family === "Deals" ? count(dealCounts.verified) : null,
      yieldLabel: family === "Deals" ? "verified offers" : "reported listings",
      // Raw errors, rejected-map keys, URLs, notes and payloads never leave the loader.
      failed: family === "Deals" ? !!row.last_status && !["ok", "empty"].includes(String(row.last_status)) : family === "News" ? !!row.last_error : false,
    }
  }))
}

export async function getDatabaseEvidence() {
  const access = await operationsAccess()
  if (access !== "allowed") return { access }
  const db = client()
  if (!db) return { access: "allowed" as const, available: false as const }
  const [discovery, deals, news, venues, activities, events, hidden, unmatched] = await Promise.all([
    sourceRows(db, "Discovery"), sourceRows(db, "Deals"), sourceRows(db, "News"),
    read(db.from("venues").select("id", { count: "exact", head: true }).eq("public_visible", true).abortSignal(AbortSignal.timeout(10_000)), total),
    read(db.from("current_activities").select("id", { count: "exact", head: true }).abortSignal(AbortSignal.timeout(10_000)), total),
    read(db.from("upcoming_events").select("id", { count: "exact", head: true }).abortSignal(AbortSignal.timeout(10_000)), total),
    read(db.from("venues").select("id", { count: "exact", head: true }).eq("public_visible", false).abortSignal(AbortSignal.timeout(10_000)), total),
    read(db.from("collected_events").select("id", { count: "exact", head: true }).is("venue_id", null).is("withdrawn_at", null).abortSignal(AbortSignal.timeout(10_000)), total),
  ])
  return { access: "allowed" as const, available: true as const, discovery, deals, news, venues, activities, events, hidden, unmatched, fetchedAt: new Date().toISOString() }
}

export type ReviewRow = { id: string; title: string; postcode: string | null; venue: string | null; address: string | null;
  source: string | null; sourceUrl: string | null; detailUrl: string | null; observed: string | null;
  status: string | null; age: string | null; start: string | null; end: string | null; recurrence: string | null; schedule: string | null }

export async function getReviewQueue(kind?: string | string[], page?: string | string[]) {
  const access = await operationsAccess()
  if (access !== "allowed") return { access }
  const selection = reviewQuery(kind, page)
  const db = client()
  if (!db) return { access: "allowed" as const, ...selection, result: unavailable }
  const venue = selection.kind === "venues"
  let query = venue ? db.from("venues").select("id,venue_name,venue_label,address,postcode,source,source_url,discovered_source_url,discovered_at,discovery_status", { count: "exact" }).eq("public_visible", false)
    // Owner, 22 Oct 2026: arcades the evidence already decided (adult_only set) never need review, and
    // arcades hidden by that day's rule stay out of the queue until the owner works through them;
    // removing the second filter then shows exactly the undecided arcades. Prison and YOI libraries
    // hidden as not open to the public (#92) are decided, so they never queue either.
    .or('category.neq."Amusement arcade",adult_only.is.null')
    .or('review_reason.is.null,review_reason.not.ilike."*2026-10-22 owner rule: amusement arcades*"')
    .or('review_reason.is.null,review_reason.not.ilike."*Owner decision 2026-10-22: not open to the public*"').order("discovered_at", { ascending: false, nullsFirst: false }) :
    db.from("collected_events").select("id,title,venue_name,venue_address,postcode,source_url,event_url,last_verified_at,listing_type,age_range,start_date,end_date,recurrence,schedule_text", { count: "exact" }).is("venue_id", null).is("withdrawn_at", null).eq("listing_type", selection.kind === "activities" ? "activity" : "event").order("last_verified_at", { ascending: false, nullsFirst: false })
  query = query.order("id").range((selection.page - 1) * PAGE_SIZE, selection.page * PAGE_SIZE - 1).abortSignal(AbortSignal.timeout(10_000))
  const result = await read(query, response => {
    const records = rows(response)
    const all = total(response)
    if (records.length !== Math.min(PAGE_SIZE, Math.max(0, all - (selection.page - 1) * PAGE_SIZE))) throw new Error("Incomplete queue")
    return { total: all, rows: records.map((row): ReviewRow => {
      if (typeof row.id !== "string" || (venue ? row.venue_name !== null && typeof row.venue_name !== "string" : typeof row.title !== "string")) throw new Error("Invalid candidate")
      // An unnamed place shows its derived display label (e.g. "Church Lane Playground"), marked as
      // derived; `venue` keeps the raw source name as identity evidence.
      const label = text(row.venue_label)?.trim()
      return { id: row.id, title: venue ? text(row.venue_name)?.trim() || (label ? `${label} (derived label; no source name)` : "Unnamed venue — identity evidence missing") : String(row.title), postcode: text(row.postcode), venue: text(row.venue_name), address: text(venue ? row.address : row.venue_address),
        source: text(row.source), sourceUrl: text(row.source_url), detailUrl: text(venue ? row.discovered_source_url : row.event_url), observed: text(venue ? row.discovered_at : row.last_verified_at),
        status: text(venue ? row.discovery_status : row.listing_type), age: text(row.age_range), start: text(row.start_date), end: text(row.end_date), recurrence: text(row.recurrence), schedule: text(row.schedule_text) }
    }) }
  })
  return { access: "allowed" as const, ...selection, result }
}

import Link from "next/link"
import { notFound, redirect } from "next/navigation"
import { getSupabase } from "@/lib/supabase"
import { operationsAccess } from "@/lib/operations/session"
import { reviewIdentity } from "@/lib/operations/reviewer"
import { validId } from "@/lib/operations/review-token"
import { evidenceUrl } from "@/lib/operations/evidence-shared"
import { pageMetadata } from "@/lib/seo"
import ReviewForm from "./review-form"

export const dynamic = "force-dynamic"
export const metadata = pageMetadata("Review a decision", "/ops/decision", "Dadspace guarded evidence decisions", { noIndex: true })
type Params = { record?: string; kind?: string; search?: string }
export default async function DecisionPage({ searchParams }: { searchParams: Promise<Params> }) {
  const access = await operationsAccess()
  if (access === "sign-in") redirect("/auth/login?next=%2Fops%2Freview")
  if (access === "denied") notFound()
  const identity = access === "allowed" ? await reviewIdentity() : null
  if (!identity || !process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY) return <section className="rounded-2xl border p-6"><h1 className="text-3xl font-bold">Decision evidence unavailable</h1><p className="mt-3">Sign-in or the review service could not be verified. No change made.</p></section>
  const params = await searchParams
  if (!validId(params.record)) notFound()
  const record = params.record
  const rollback = params.kind === "rollback"
  const listing = params.kind === "activities" || params.kind === "events"
  try {
    const db = getSupabase()
    if (!db) throw new Error("Unavailable")
    const table = rollback ? "operations_review_audit" : listing ? "collected_events" : "venues"
    const projection = rollback ? "id,action,reason,created_at,reverted_by" : listing ? "id,title,venue_name,venue_address,postcode,listing_type,start_date,end_date,recurrence,schedule_text,age_range,source_url,event_url,venue_id,withdrawn_at" :
      "id,venue_name,address,postcode,website,source_url,public_visible,discovery_status,merged_into"
    const read = await db.from(table).select(projection).eq("id", record).maybeSingle().abortSignal(AbortSignal.timeout(10_000))
    if (read.error || !read.data) throw new Error("Unavailable")
    const row = read.data as unknown as Record<string, unknown>
    const search = typeof params.search === "string" ? params.search.trim().slice(0, 100) : ""
    let targets: { id: string; venue_name: string; postcode: string | null }[] = []
    let targetError = false
    if (!rollback && (search.length >= 2 || typeof row.postcode === "string")) {
      let query = db.from("venues").select("id,venue_name,postcode").eq("public_visible", true).is("merged_into", null).neq("id", record)
      query = search.length >= 2 ? query.ilike("venue_name", `%${search.replace(/[\\%_]/g, "\\$&")}%`) : query.eq("postcode", row.postcode)
      const candidates = await query.order("venue_name").order("id").limit(20).abortSignal(AbortSignal.timeout(10_000))
      targetError = !!candidates.error || !Array.isArray(candidates.data)
      if (!targetError) targets = candidates.data as typeof targets
    }
    const history = await db.from("operations_review_audit").select("id,actor_id,action,reason,created_at,reverted_by").eq("record_id", record).order("created_at", { ascending: false }).order("id").limit(20).abortSignal(AbortSignal.timeout(10_000))
    const title = rollback ? `Rollback: ${String(row.action)}` : String(listing ? row.title : row.venue_name)
    const url = evidenceUrl(row.source_url)
    const detail = evidenceUrl(row.event_url)
    return <div className="space-y-6">
      <header><Link className="font-semibold underline" href="/ops/review">Back to review queues</Link><h1 className="mt-4 break-words text-3xl font-bold">{title}</h1><p className="mt-3 text-muted-foreground">{identity.reviewer ? "Reviewer access" : "Read-only operator · decision previews available"}. Review evidence and preview consequences before applying. No decision is made by opening this page.</p></header>
      <section className="rounded-2xl border bg-card p-6 space-y-3"><h2 className="text-xl font-bold">Current evidence</h2><p className="break-words">{[row.venue_name, row.address || row.venue_address, row.postcode].filter(Boolean).map(String).join(" · ") || "See original decision evidence"}</p>{listing && <><p>{String(row.start_date || "No published start date")} → {String(row.end_date || "No published end date")}</p><p>{String(row.age_range || "Ages missing")} · {String(row.recurrence || "Recurrence missing")}</p><p className="whitespace-pre-wrap break-words">{String(row.schedule_text || "Schedule missing")}</p></>}{rollback && <p>{String(row.reason)}</p>}<div className="flex flex-wrap gap-4">{url && <a href={url} target="_blank" rel="noopener noreferrer" className="underline">Source evidence</a>}{detail && <a href={detail} target="_blank" rel="noopener noreferrer" className="underline">Listing detail</a>}</div></section>
      {!rollback && <section className="rounded-2xl border bg-card p-6"><h2 className="text-xl font-bold">Canonical venue candidates</h2><p className="mt-2 text-sm text-muted-foreground">Possible shared-postcode venues are shown by default. Search returns at most 20 public canonical records. Names and postcodes alone do not prove identity.</p><form className="mt-4 flex flex-wrap gap-3"><input type="hidden" name="record" value={record}/><input type="hidden" name="kind" value={params.kind || "venues"}/><label className="min-w-0 flex-1">Venue name<input name="search" defaultValue={search} minLength={2} maxLength={100} className="mt-1 block w-full rounded-lg border bg-background p-3"/></label><button className="self-end rounded-lg border px-4 py-3 font-semibold">Find candidates</button></form>{targetError && <p role="status" className="mt-3">Candidate evidence unavailable. This does not establish no matching venues.</p>}{!targetError && targets.length === 0 && <p className="mt-3 text-sm">No candidates in this bounded search. Try a different evidenced name; retain useful listings while unresolved.</p>}</section>}
      <ReviewForm key={`${record}-${search}`} record={record} listing={listing} rollback={rollback} reviewer={identity.reviewer} targets={targets}/>
      <section className="rounded-2xl border bg-card p-6"><h2 className="text-xl font-bold">Recent decision history</h2><p className="mt-2 text-sm text-muted-foreground">Up to 20 decisions. Actor identifiers are recorded from verified sign-in; rollback is blocked after affected records change.</p>{history.error || !Array.isArray(history.data) ? <p role="status">History unavailable. Check before retrying a decision.</p> : history.data.length === 0 ? <p className="mt-3">No decisions recorded for this record.</p> : <ul className="mt-4 space-y-4">{history.data.map(item => <li key={item.id} className="break-words border-t pt-3"><p className="font-semibold">{item.action} · {item.created_at}</p><p>{item.reason}</p><p className="break-all text-xs">Reviewer: {item.actor_id}</p>{item.action !== "rollback" && !item.reverted_by && <Link className="mt-2 inline-block font-semibold underline" href={`/ops/decision?kind=rollback&record=${item.id}`}>Preview rollback</Link>}{item.reverted_by && <p className="text-sm">Rolled back; original evidence retained.</p>}</li>)}</ul>}</section>
    </div>
  } catch { return <section className="rounded-2xl border p-6"><h1 className="text-3xl font-bold">Decision evidence unavailable</h1><p className="mt-3">The record could not be loaded. Refresh the queue and try again; no change made.</p><Link href="/ops/review" className="mt-4 inline-block underline">Back to queues</Link></section> }
}

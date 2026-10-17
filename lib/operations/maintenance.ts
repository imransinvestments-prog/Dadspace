import "server-only"
import { createHash } from "node:crypto"
import { createClient } from "@/lib/supabase/server"
import { getSupabase } from "@/lib/supabase"
import { isOperationsOwner, isOperationsUser } from "./access"
import { maintenanceIntent, signMaintenance, verifyMaintenance, type MaintenanceIntent } from "./maintenance-token"

const API = "https://api.github.com/repos/imransinvestments-prog/Dadspace"
export async function maintenanceIdentity() {
  try {
    const { data, error } = await (await createClient()).auth.getUser()
    if (error || !data.user || !isOperationsOwner(data.user)) return null
    return { id: data.user.id, maintainer: isOperationsUser(data.user.id, process.env.DADSPACE_MAINTAINER_USER_IDS) }
  } catch { return null }
}
export function maintenanceConfiguration() {
  return {
    live: process.env.VERCEL_ENV === "production" && process.env.DADSPACE_MAINTENANCE_ENABLED === "true",
    signing: (process.env.DADSPACE_MAINTENANCE_SIGNING_KEY?.length || 0) >= 32,
    database: !!process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY,
    dispatch: !!process.env.DADSPACE_MAINTENANCE_GITHUB_TOKEN,
  }
}
async function github(path: string, body?: unknown) {
  const key = process.env.DADSPACE_MAINTENANCE_GITHUB_TOKEN
  const response = await fetch(`${API}${path}`, { method: body ? "POST" : "GET", cache: "no-store", redirect: "error", signal: AbortSignal.timeout(15_000),
    headers: { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", ...(key ? { Authorization: `Bearer ${key}` } : {}), ...(body ? { "Content-Type": "application/json" } : {}) }, ...(body ? { body: JSON.stringify(body) } : {}) })
  if (!response.ok) throw new Error("Runner evidence or dispatch unavailable")
  return response.status === 204 ? null : response.json()
}
function database() {
  const db = getSupabase()
  if (!process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY || !db) throw new Error("Maintenance database unavailable")
  return db
}
export async function maintenancePlan(intent: MaintenanceIntent) {
  const db = database()
  if (intent.action === "reconcile") {
    const { data: audit, error } = await db.from("operations_maintenance_audit").select("id,status,family,action,run_id,after_state").eq("id", intent.record).single()
    if (error || !audit || audit.action !== "retry" || audit.family !== intent.family || audit.status === "reconciled" || (audit.run_id && String(audit.run_id) !== intent.runId)) throw new Error("Unresolved dispatch unavailable")
    const run = await github(`/actions/runs/${intent.runId}`)
    const expected = intent.family === "news" ? ".github/workflows/news.yml" : ".github/workflows/original-content.yml"
    if (run?.event !== "workflow_dispatch" || run.head_branch !== "main" || run.status !== "completed" || run.path !== expected || !String(run.display_title).includes(intent.record)) throw new Error("Completed matching run required; never clear an unproven dispatch")
    const state = JSON.stringify({ audit, runId: run.id, conclusion: run.conclusion, updated: run.updated_at })
    return { fingerprint: createHash("sha256").update(state).digest("hex"), description: `Reconcile request ${intent.record} with completed run ${run.id}: ${run.conclusion}. This never reruns the worker.`, cost: "No model call. Recovery audit retains the matching runner outcome." }
  }
  if (intent.action !== "retry") {
    const { data, error } = await db.rpc("dadspace_maintenance_plan", { p_action: intent.action, p_family: intent.family, p_record: intent.record }).abortSignal(AbortSignal.timeout(10_000))
    if (error || !data || !/^[a-f0-9]{32}$/.test(data.fingerprint)) throw new Error("Plan unavailable or stale")
    return { fingerprint: data.fingerprint as string, description: `${intent.action}: ${String(data.title || intent.record)}`, cost: "No model call. One record changes; restore is blocked if newer facts exist." }
  }
  // News retry is one currently active source, at most 10 candidates / five minutes.
  // Originals retry is one current slot, at most two drafts + two reviews.
  if (intent.family === "news") {
    const { data, error } = await db.from("news_sources").select("id,name,feed_url,active,last_checked_at,consecutive_failures").eq("id", intent.record).eq("active", true).single()
    if (error || !data) throw new Error("Active source unavailable")
    const state = JSON.stringify({ source: data, dryRun: intent.dryRun, maxCandidates: 10, minutes: 5 })
    return { fingerprint: createHash("sha256").update(state).digest("hex"), description: `Retry one active News source: ${data.name}; up to 10 candidates, five minutes.`, cost: "Dry run still calls the model. Billed amount unknown; live dispatch requires the approved retry policy." }
  }
  const [cadence, ...dateParts] = intent.record.split("-")
  const date = dateParts.join("-")
  const localDate = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date())
  if (date !== localDate || (cadence === "weekly" && new Date(`${date}T12:00:00Z`).getUTCDay() !== 5)) throw new Error("Retry only today's due slot")
  const { data, error } = await db.from("original_posts").select("slug").eq("cadence", cadence).eq("slot_date", date)
  if (error || data?.length) throw new Error("Slot exists or cannot be verified; no generation allowed")
  const state = JSON.stringify({ slot: intent.record, dryRun: intent.dryRun, maxModelCalls: 4 })
  return { fingerprint: createHash("sha256").update(state).digest("hex"), description: `Retry ${intent.record}: two drafts maximum, independent review, no duplicate publication.`, cost: "Up to four model requests. Billed amount unknown; paid retry policy approval required." }
}
export async function previewMaintenance(value: unknown) {
  const identity = await maintenanceIdentity()
  if (!identity) throw new Error("Owner access required")
  const intent = maintenanceIntent(value)
  if (!intent) throw new Error("Invalid intent")
  const plan = await maintenancePlan(intent)
  const config = maintenanceConfiguration()
  const token = config.signing ? signMaintenance(intent, identity.id, plan.fingerprint, process.env.DADSPACE_MAINTENANCE_SIGNING_KEY!) : null
  return { ...plan, token, canApply: !!token && config.live && identity.maintainer && config.database && (intent.action !== "retry" || config.dispatch) }
}
export async function applyMaintenance(token: unknown) {
  const identity = await maintenanceIdentity(), config = maintenanceConfiguration()
  if (!identity?.maintainer || !config.live || !config.signing || !config.database) throw new Error("Maintenance disabled or not authorized")
  const intent = verifyMaintenance(token, identity.id, process.env.DADSPACE_MAINTENANCE_SIGNING_KEY!)
  if (!intent) throw new Error("Invalid or expired preview")
  const db = database()
  if (intent.action === "reconcile") {
    const plan = await maintenancePlan(intent)
    if (plan.fingerprint !== intent.fingerprint) throw new Error("Recovery evidence changed")
    const { data: current, error: readError } = await db.from("operations_maintenance_audit").select("status,after_state").eq("id", intent.record).single()
    if (readError || !current || current.status === "reconciled") throw new Error("Recovery unavailable")
    const { data, error } = await db.from("operations_maintenance_audit").update({ status: "reconciled", run_id: Number(intent.runId), after_state: { ...current.after_state, reconciliation: { actor: identity.id, reason: intent.reason, run_id: intent.runId, verified_at: new Date().toISOString() } } }).eq("id", intent.record).eq("status", current.status).select("id")
    if (error || data?.length !== 1) throw new Error("Recovery not confirmed")
    return intent.record
  }
  if (intent.action !== "retry") {
    const { data, error } = await db.rpc("dadspace_maintenance_apply", { p_actor: identity.id, p_request: intent.request, p_action: intent.action, p_family: intent.family, p_record: intent.record, p_expected: intent.fingerprint, p_reason: intent.reason })
    if (error || data !== intent.request) throw new Error("Could not confirm apply; inspect audit before retry")
    return intent.request
  }
  if (!config.dispatch || process.env.DADSPACE_MAINTENANCE_RETRY_POLICY !== "bounded-news-originals-v1") throw new Error("Retry policy not approved")
  // A timed-out dispatch is never automatically repeated. Audit is written first.
  const plan = await maintenancePlan(intent)
  if (plan.fingerprint !== intent.fingerprint) throw new Error("Preview changed")
  const workflow = intent.family === "news" ? "news.yml" : "original-content.yml"
  const running = await github(`/actions/workflows/${workflow}/runs?branch=main&per_page=20`)
  if (!Array.isArray(running?.workflow_runs) || running.workflow_runs.some((run: { status: string }) => run.status !== "completed")) throw new Error("Runner busy or unknown")
  const inputs = intent.family === "news" ? { dry_run: String(intent.dryRun), source_id: intent.record, max_new: "10", max_minutes: "5", maintenance_request: intent.request } :
    { dry_run: intent.dryRun, cadence: intent.record.startsWith("weekly") ? "weekly" : "daily", slot_date: intent.record.replace(/^(daily|weekly)-/, ""), maintenance_request: intent.request }
  const { data: claimed, error } = await db.rpc("dadspace_maintenance_claim", { p_actor: identity.id, p_request: intent.request, p_family: intent.family, p_record: intent.record, p_reason: intent.reason, p_scope: { fingerprint: plan.fingerprint, inputs } })
  if (error) throw new Error("Could not claim dispatch")
  if (!claimed) return intent.request
  let status = "uncertain"
  try { await github(`/actions/workflows/${workflow}/dispatches`, { ref: "main", inputs }); status = "submitted" }
  finally {
    const result = await db.from("operations_maintenance_audit").update({ status }).eq("id", intent.request).eq("status", "claimed")
    if (result.error) throw new Error("Dispatch outcome unknown; reconcile audit and runner before another request")
  }
  return intent.request
}

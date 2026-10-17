import "server-only"
import { createHash } from "node:crypto"
import { getSupabase } from "@/lib/supabase"
import { getDeals } from "@/lib/deals"
import { operationsAccess } from "./session"
import { OPERATIONS_PROCESSES } from "./processes"
import { reviewTask } from "./review-tasks"
import { NEWS_SAMPLE } from "./news-sample"
import historical from "@/artefacts/data/ds10-remaining-source-review-2026-10-12.json"
import manifest1 from "@/artefacts/shadow-cohorts/quality-2026-10-15/manifest-001.json"
import manifest2 from "@/artefacts/shadow-cohorts/quality-2026-10-15/manifest-002.json"
import manifest3 from "@/artefacts/shadow-cohorts/quality-2026-10-15/manifest-003.json"
import manifest4 from "@/artefacts/shadow-cohorts/quality-2026-10-15/manifest-004.json"
import sample1 from "@/artefacts/shadow-cohorts/quality-2026-10-15/sample-001.json"
import sample2 from "@/artefacts/shadow-cohorts/quality-2026-10-15/sample-002.json"
import sample3 from "@/artefacts/shadow-cohorts/quality-2026-10-15/sample-003.json"
import sample4 from "@/artefacts/shadow-cohorts/quality-2026-10-15/sample-004.json"

export type MaterialRow = { id: string; title: string; fields: Record<string, unknown> }
export type ReviewMaterial = { available: boolean; label: string; notice: string; rows: MaterialRow[]; total: number; page: number }
export const MATERIAL_PAGE_SIZE = 10
export function materialPage(value: unknown) { return typeof value === "string" && /^[1-9]\d{0,3}$/.test(value) ? Number(value) : 1 }
export function materialFingerprint(row: MaterialRow) { return createHash("sha256").update(JSON.stringify(row)).digest("hex") }
export const REVIEW_RUBRIC = [
  { id: "scope", title: "Settled pilot scope", fields: { geography: "W3 9LN, 10 km", ages: "0–5 inclusive", owner: "Imran Tajuddin", instruction: "Keep useful wider-age and national supply; score it separately." } },
  { id: "venues", title: "Venue quality gate", fields: { denominator: "50 pilot venues from the agreed #122 cohort", target: "At least 95% correct identity/location and usable evidence; zero hidden leakage", check: "Opening/access facts, official sources and image rights; unknown stays unknown." } },
  { id: "news", title: "News quality gate", fields: { denominator: "50 agreed news items", target: "90% relevant and correctly attributed; 95% working destinations", check: "Summaries, dates, sensitive-story labels and homepage picks." } },
  { id: "deals", title: "Deals value gate", fields: { denominator: "Entire published pool plus top 20; agree any smaller denominator", target: "90% useful published offers; 18/20 useful top offers; zero known expired or unsupported savings", check: "Exact redemption, stock, costs, expiry, terms and comparison basis; preserve merchant-advertised-sale disclosure." } },
  { id: "activities", title: "Activity coverage decision", fields: { denominator: "100 agreed activities", target: "At least 90% relevant, current and actionable", proposed: "10 distinct actionable activities, three categories and two independent providers per pilot area; this coverage target still requires agreement", check: "Dates, recurrence, ages, canonical place, sources and scheduled freshness evidence." } },
] satisfies MaterialRow[]

function slice(rows: MaterialRow[], page: number, label: string, notice: string): ReviewMaterial {
  return { available: true, label, notice, rows: rows.slice((page - 1) * MATERIAL_PAGE_SIZE, page * MATERIAL_PAGE_SIZE), total: rows.length, page }
}
export async function getReviewMaterial(id: number, page = 1): Promise<ReviewMaterial> {
  if (!reviewTask(id) || !Number.isSafeInteger(page) || page < 1 || page > 9999 || await operationsAccess() !== "allowed") throw new Error("Review access denied")
  if (id === 126) return slice(NEWS_SAMPLE.rows, page, "Fixed 50-article quality sample", `Frozen on ${NEWS_SAMPLE.frozen_on} from ${NEWS_SAMPLE.pool_count} published articles, covering categories and geographic scopes. New articles do not change this sample. Your two previously reviewed records are retained. Review usefulness for the intended area, attribution and working links; local does not mean irrelevant.`)
  if (id === 149) return slice(OPERATIONS_PROCESSES.map((p, index) => ({ id: `process-${index + 1}`, title: p.name, fields: { owner: p.owner, permission: p.permission, cadence: p.cadence, evidence: p.evidence, outstanding_work: p.next, evidence_url: p.href } })), page, "Upkeep process inventory", "Review each process and its outstanding capability. Live source counts and health are shown below. Configuration text alone does not prove a working recovery path.")
  if (id === 123) return slice(REVIEW_RUBRIC, page, "Quality and coverage decisions", "Review each threshold and record your exact agreement or requested change. The pilot scope is already settled. Numeric gates must be checked against current task criteria; this is not a completed sample review.")
  if (id === 135) return slice(historical.records.map(row => ({ id: row.record_id, title: row.title, fields: { checked_on: row.checked_on, status: row.status, recommendation: row.recommendation, remaining: row.remaining, links: row.links } })), page, "Retained source proposals", "Saved evidence from 12 October 2026, not current source verification. These are the remaining source proposals, not the full 201-proposal / 191-record queues. Recording a decision does not apply a database correction.")
  if (id === 145) return slice([manifest1, manifest2, manifest3, manifest4].map((manifest, index) => ({ id: `provider-sample-${index + 1}`, title: `Provider source sample ${index + 1}`, fields: { reviewer: manifest.reviewer, candidates: manifest.chunks, source_text: [sample1, sample2, sample3, sample4][index].prompt.split("\nCONTENT:\n").at(-1) } })), page, "Saved provider source samples", "Four purposive source samples and AI-labelled expected candidates from 15 October. Provider response comparisons, billed costs and representative coverage are not supplied by this view; do not approve rollout from this source material alone.")
  const label = id === 34 ? "Published venues" : id === 126 ? "Published news articles" : id === 128 ? "Published Originals" : id === 130 ? "Current public deals in selector order" : "Current activities"
  const notice = "Live browsing records, not a frozen #122 acceptance cohort. National/wider-age records may be included. Record-level decisions retain the displayed snapshot; they do not establish overall pilot acceptance."
  const unavailable: ReviewMaterial = { available: false, label, notice: "Data could not be loaded. This is not an empty review queue. Check the server database configuration and retry.", rows: [], total: 0, page }
  if (!process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY) return unavailable
  try {
    if (id === 130) {
      const result = await getDeals()
      if (result.loadFailed) return unavailable
      return slice(result.items.map((row, index) => ({ id: String(row.id), title: row.title, fields: { rank: index + 1, retailer: row.retailer, description: row.description, price: row.price, was_price: row.was_price, discount_pct: row.discount_pct, display_group: row.display_group, value_band: row.value_band, expires_at: row.expires_at, last_seen: row.last_seen, link: row.link } })), page, label, notice)
    }
    const db = getSupabase()
    if (!db) return unavailable
    const [table, columns, order] = id === 34 ? ["venues", "id,venue_name,category,address,postcode,website,access,fee,opening_hours,source_url,image_source_url,image_attribution,image_license,discovery_status", "venue_name"] : id === 126 ? ["feed_items", "id,title,url,source_name,published_at,summary,why_it_matters,category,relevance", "published_at"] : id === 128 ? ["original_posts", "slug,title,cadence,summary,sections,published_at", "published_at"] : ["current_activities", "id,title,description,category,age_range,schedule_text,time_text,start_date,end_date,cost_text,recurrence,venue_name,venue_address,postcode,source_url,event_url,last_verified_at", "title"]
    let query = db.from(table).select(columns, { count: "exact" })
    if (id === 34) query = query.eq("public_visible", true)
    if (id === 128) query = query.lte("published_at", new Date().toISOString())
    const result = await query.order(order, { ascending: order !== "published_at", nullsFirst: false }).order(id === 128 ? "slug" : "id").range((page - 1) * MATERIAL_PAGE_SIZE, page * MATERIAL_PAGE_SIZE - 1).abortSignal(AbortSignal.timeout(10000))
    if (result.error || !Array.isArray(result.data) || result.count === null) return unavailable
    const records = result.data as unknown as Record<string, unknown>[]
    if (records.length !== Math.min(MATERIAL_PAGE_SIZE, Math.max(0, result.count - (page - 1) * MATERIAL_PAGE_SIZE))) return unavailable
    return { available: true, label, notice: id === 128 ? `${notice} Rejected drafts are retained in worker artifacts and are not connected here; review those before overall editorial acceptance.` : notice, total: result.count, page, rows: records.map(row => ({ id: String(row.id ?? row.slug), title: String(row.title ?? row.venue_name), fields: row })) }
  } catch { return unavailable }
}

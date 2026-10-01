import "server-only"
import { getSupabase } from "./supabase"
import type { DadActivity } from "./types"

export const ACTIVITY_PAGE_SIZE = 24
const MAX_CATEGORY_ROWS = 1000
const text = (value: unknown) => (typeof value === "string" && value.trim() ? value.trim() : null)

function toActivity(row: Record<string, unknown>): DadActivity {
  return {
    id: String(row.id),
    title: String(row.title ?? "Family activity"),
    description: text(row.description),
    schedule_text: text(row.schedule_text),
    time_text: text(row.time_text),
    location: text(row.location),
    event_url: text(row.event_url),
    cost_text: text(row.cost_text),
    age_range: text(row.age_range),
    family_relevance: typeof row.family_relevance === "number" ? row.family_relevance : null,
    source_url: text(row.source_url),
    source_id: row.source_id == null ? null : String(row.source_id),
    category: text(row.category),
    venue_name: text(row.venue_name),
    venue_address: text(row.venue_address),
    postcode: text(row.postcode),
    venue_id: row.venue_id == null ? null : String(row.venue_id),
    last_seen_at: text(row.last_seen_at),
  }
}

function safeSearch(value: string | null | undefined) {
  return (value ?? "").trim().replace(/[,%()]/g, " ").replace(/\s+/g, " ").slice(0, 100)
}

export type ActivityPage = {
  activities: DadActivity[]
  total: number
  offset: number
  limit: number
  hasMore: boolean
}

export async function fetchActivityPage(options?: {
  offset?: number
  limit?: number
  query?: string | null
  category?: string | null
}): Promise<ActivityPage> {
  const db = getSupabase()
  const offset = Math.max(0, options?.offset ?? 0)
  const limit = Math.min(48, Math.max(1, options?.limit ?? ACTIVITY_PAGE_SIZE))
  if (!db) return { activities: [], total: 0, offset, limit, hasMore: false }

  let request = db
    .from("current_activities")
    .select("*", { count: "exact" })
    .order("family_relevance", { ascending: false })
    .order("title", { ascending: true })
    .range(offset, offset + limit - 1)

  const category = (options?.category ?? "").trim()
  if (category && category !== "all") request = request.eq("category", category)

  const query = safeSearch(options?.query)
  if (query) {
    const pattern = `%${query}%`
    request = request.or(
      `title.ilike.${pattern},venue_name.ilike.${pattern},location.ilike.${pattern},postcode.ilike.${pattern},age_range.ilike.${pattern},schedule_text.ilike.${pattern}`,
    )
  }

  const { data, error, count } = await request
  if (error || !data) {
    if (error) console.error("Failed to load activities:", error.message)
    return { activities: [], total: 0, offset, limit, hasMore: false }
  }

  const activities = data.map((row) => toActivity(row as Record<string, unknown>))
  const total = count ?? activities.length
  return { activities, total, offset, limit, hasMore: offset + activities.length < total }
}

export async function fetchActivityCategories(): Promise<string[]> {
  const db = getSupabase()
  if (!db) return []
  const { data, error } = await db
    .from("current_activities")
    .select("category")
    .not("category", "is", null)
    .limit(MAX_CATEGORY_ROWS)
  if (error || !data) return []
  return [...new Set(data.map((row) => text(row.category)).filter((value): value is string => !!value))].sort()
}

export async function fetchActivityById(id: string): Promise<DadActivity | null> {
  const db = getSupabase()
  if (!db || !id) return null
  const { data, error } = await db
    .from("current_activities")
    .select("*")
    .eq("id", id)
    .limit(1)
    .maybeSingle()
  if (error || !data) return null
  return toActivity(data as Record<string, unknown>)
}

export async function fetchSimilarActivities(activity: DadActivity, limit = 6): Promise<DadActivity[]> {
  const db = getSupabase()
  if (!db) return []
  let request = db
    .from("current_activities")
    .select("*")
    .neq("id", activity.id)
    .order("family_relevance", { ascending: false })
    .order("title", { ascending: true })
    .limit(Math.min(12, Math.max(limit, 1)))
  if (activity.category) request = request.eq("category", activity.category)
  const { data, error } = await request
  if (error || !data) return []
  return data.map((row) => toActivity(row as Record<string, unknown>)).slice(0, limit)
}

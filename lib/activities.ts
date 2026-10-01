import "server-only"
import { getSupabase } from "./supabase"
import type { DadActivity } from "./types"

const MAX_ACTIVITIES = 500
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

export async function fetchCurrentActivities(): Promise<DadActivity[]> {
  const db = getSupabase()
  if (!db) return []
  const { data, error } = await db
    .from("current_activities")
    .select("*")
    .order("family_relevance", { ascending: false })
    .order("title", { ascending: true })
    .limit(MAX_ACTIVITIES)
  if (error || !data) {
    if (error) console.error("Failed to load activities:", error.message)
    return []
  }
  return data.map((row) => toActivity(row as Record<string, unknown>))
}

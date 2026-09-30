import "server-only"
import { getSupabase } from "./supabase"
import { londonToday, upcomingWeekend } from "./dates"
import { sampleEvents } from "./sample-data"
import type { DadEvent } from "./types"

const MAX_EVENTS = 500
const IMAGE_KEYS = ["image_url", "image", "thumbnail_url", "photo_url", "og_image"] as const

function imageFrom(row: Record<string, unknown>): string | null {
  for (const key of IMAGE_KEYS) {
    const value = row[key]
    if (typeof value === "string" && /^https:\/\/\S+$/i.test(value.trim())) return value.trim()
  }
  return null
}

const text = (value: unknown) => (typeof value === "string" && value.trim() ? value.trim() : null)

function toEvent(row: Record<string, unknown>): DadEvent {
  return {
    id: String(row.id),
    title: String(row.title ?? "Family event"),
    description: text(row.description),
    start_date: String(row.start_date),
    end_date: text(row.end_date),
    time_text: text(row.time_text),
    location: text(row.location),
    event_url: text(row.event_url),
    cost_text: text(row.cost_text),
    age_range: text(row.age_range),
    family_relevance: typeof row.family_relevance === "number" ? row.family_relevance : null,
    source_url: text(row.source_url),
    image_url: imageFrom(row),
  }
}

export type EventsListing = { events: DadEvent[]; today: string; saturday: string; sunday: string; isSample: boolean }

export async function fetchUpcomingEvents(): Promise<EventsListing> {
  const today = londonToday()
  const { saturday, sunday } = upcomingWeekend(today)
  const db = getSupabase()

  if (db) {
    // `*` so any image column added to the table later is picked up without a code change.
    const { data, error } = await db
      .from("upcoming_events")
      .select("*")
      .gte("end_date", today)
      .order("start_date", { ascending: true })
      .order("family_relevance", { ascending: false })
      .limit(MAX_EVENTS)
    if (!error && data?.length) {
      return { events: data.map((row) => toEvent(row as Record<string, unknown>)), today, saturday, sunday, isSample: false }
    }
  }

  return { events: sampleEvents(saturday, sunday), today, saturday, sunday, isSample: true }
}

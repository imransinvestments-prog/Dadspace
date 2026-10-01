import "server-only"
import { getSupabase } from "./supabase"
import { londonToday, upcomingWeekend } from "./dates"
import { sampleEvents } from "./sample-data"
import { eventCategory } from "./event-meta"
import type { DadEvent } from "./types"

const MAX_EVENTS = 500
const IMAGE_KEYS = ["image_url", "image", "thumbnail_url", "photo_url", "og_image"] as const
const PROTECTED_RECURRING = /\b(weekly|every\s+(?:mon|tue|wed|thu|fri|sat|sun)|term[- ]?time|class|lesson|session|club|course)\b/i

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
    source_id: row.source_id == null ? null : String(row.source_id),
    recurrence: text(row.recurrence),
    image_url: imageFrom(row),
  }
}

function normalise(value: string | null | undefined) {
  return (value ?? "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\b(the|a|an)\b/g, " ")
    .replace(/\s+/g, " ")
    .trim()
}

function titleTokens(title: string) {
  const stop = new Set(["the", "and", "for", "with", "at", "in", "of", "to", "a", "an"])
  return new Set(normalise(title).split(" ").filter((word) => word.length > 1 && !stop.has(word)))
}

function similarTitle(a: string, b: string) {
  const na = normalise(a)
  const nb = normalise(b)
  if (na === nb) return true
  const aa = titleTokens(a)
  const bb = titleTokens(b)
  if (aa.size < 3 || bb.size < 3) return false
  let shared = 0
  for (const token of aa) if (bb.has(token)) shared += 1
  const union = new Set([...aa, ...bb]).size
  return union > 0 && shared / union >= 0.8
}

function sameVenue(a: DadEvent, b: DadEvent) {
  const aa = normalise(a.location)
  const bb = normalise(b.location)
  return !!aa && !!bb && aa === bb
}

function protectedRecurring(event: DadEvent) {
  if ((event.recurrence ?? "").toLowerCase() === "recurring") return true
  return PROTECTED_RECURRING.test(`${event.title} ${event.description ?? ""}`)
}

/**
 * Conservative display dedupe. It never merges recurring/weekly classes and it
 * never merges same-named events at different venues. This does not alter the
 * database; it only prevents obvious cross-source duplicates being shown twice.
 */
export function dedupeEvents(events: DadEvent[]): DadEvent[] {
  const kept: DadEvent[] = []
  for (const event of events) {
    if (protectedRecurring(event)) {
      kept.push(event)
      continue
    }
    const start = event.start_date.slice(0, 10)
    const duplicate = kept.some(
      (other) =>
        !protectedRecurring(other) &&
        other.start_date.slice(0, 10) === start &&
        sameVenue(event, other) &&
        similarTitle(event.title, other.title),
    )
    if (!duplicate) kept.push(event)
  }
  return kept
}

function locationBucket(event: DadEvent) {
  const location = (event.location ?? "").trim()
  if (!location) return `source:${event.source_id ?? "unknown"}`
  const parts = location.split(",").map((part) => part.trim()).filter(Boolean)
  const postcode = /^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/i
  const nonPostcode = parts.filter((part) => !postcode.test(part))
  if (nonPostcode.length >= 2) return normalise(nonPostcode[nonPostcode.length - 1])
  if (nonPostcode.length === 1 && parts.length > 1) return normalise(nonPostcode[0])
  return `source:${event.source_id ?? normalise(location)}`
}

/** Round-robin locations/sources while preserving each bucket's date order. */
export function geographicallyBalanceEvents(events: DadEvent[]): DadEvent[] {
  const buckets = new Map<string, DadEvent[]>()
  for (const event of events) {
    const key = locationBucket(event)
    buckets.set(key, [...(buckets.get(key) ?? []), event])
  }
  const queues = [...buckets.values()]
  const balanced: DadEvent[] = []
  let remaining = events.length
  while (remaining > 0) {
    for (const queue of queues) {
      const next = queue.shift()
      if (!next) continue
      balanced.push(next)
      remaining -= 1
    }
  }
  return balanced
}

export type EventsListing = { events: DadEvent[]; today: string; saturday: string; sunday: string; isSample: boolean }

export async function fetchUpcomingEvents(): Promise<EventsListing> {
  const today = londonToday()
  const { saturday, sunday } = upcomingWeekend(today)
  const db = getSupabase()

  if (db) {
    const { data, error } = await db
      .from("upcoming_events")
      .select("*")
      .gte("end_date", today)
      .order("start_date", { ascending: true })
      .order("family_relevance", { ascending: false })
      .limit(MAX_EVENTS)
    if (!error && data?.length) {
      const clean = dedupeEvents(data.map((row) => toEvent(row as Record<string, unknown>)))
      return { events: geographicallyBalanceEvents(clean), today, saturday, sunday, isSample: false }
    }
  }

  return { events: sampleEvents(saturday, sunday), today, saturday, sunday, isSample: true }
}

export async function fetchEventById(id: string): Promise<DadEvent | null> {
  const db = getSupabase()
  if (!db || !id) return null
  const { data, error } = await db.from("collected_events").select("*").eq("id", id).limit(1).maybeSingle()
  if (error || !data) return null
  return toEvent(data as Record<string, unknown>)
}

export async function fetchSimilarUpcomingEvents(event: DadEvent, limit = 6): Promise<DadEvent[]> {
  const db = getSupabase()
  if (!db) return []
  const today = londonToday()
  const { data, error } = await db
    .from("upcoming_events")
    .select("*")
    .gte("end_date", today)
    .neq("id", event.id)
    .order("start_date", { ascending: true })
    .order("family_relevance", { ascending: false })
    .limit(80)
  if (error || !data) return []

  const candidates = dedupeEvents(data.map((row) => toEvent(row as Record<string, unknown>)))
  const wantedCategory = eventCategory(event)
  const place = normalise(event.location)

  return candidates
    .map((candidate) => {
      let score = candidate.family_relevance ?? 0
      if (eventCategory(candidate) === wantedCategory) score += 5
      if (place && normalise(candidate.location).includes(place)) score += 4
      return { candidate, score }
    })
    .sort((a, b) => b.score - a.score || a.candidate.start_date.localeCompare(b.candidate.start_date))
    .slice(0, limit)
    .map(({ candidate }) => candidate)
}

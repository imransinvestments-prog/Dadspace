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
    start_date: text(row.start_date) ?? "",
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
    category: text(row.category),
    is_holiday_camp: row.is_holiday_camp === true,
    venue_name: text(row.venue_name),
    venue_address: text(row.venue_address),
    postcode: text(row.postcode),
    venue_id: row.venue_id == null ? null : String(row.venue_id),
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

function tokenSimilarity(a: string | null | undefined, b: string | null | undefined) {
  const aa = new Set(normalise(a).split(" ").filter(Boolean))
  const bb = new Set(normalise(b).split(" ").filter(Boolean))
  if (!aa.size || !bb.size) return 0
  let shared = 0
  for (const token of aa) if (bb.has(token)) shared += 1
  return shared / new Set([...aa, ...bb]).size
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
  const aa = normalise(a.venue_name ?? a.location)
  const bb = normalise(b.venue_name ?? b.location)
  if (!aa || !bb) return false
  return aa === bb || aa.includes(bb) || bb.includes(aa) || tokenSimilarity(aa, bb) >= 0.75
}

function protectedRecurring(event: DadEvent) {
  if ((event.recurrence ?? "").toLowerCase() === "recurring") return true
  return PROTECTED_RECURRING.test(`${event.title} ${event.description ?? ""}`)
}

function sameExactListingOccurrence(a: DadEvent, b: DadEvent) {
  return (
    !!a.event_url &&
    !!b.event_url &&
    a.event_url === b.event_url &&
    a.start_date.slice(0, 10) === b.start_date.slice(0, 10) &&
    sameVenue(a, b)
  )
}

/** Conservative display dedupe for legacy Event rows. */
export function dedupeEvents(events: DadEvent[]): DadEvent[] {
  const kept: DadEvent[] = []
  for (const event of events) {
    const duplicate = kept.some((other) => {
      if (sameExactListingOccurrence(event, other)) return true
      if (protectedRecurring(event) || protectedRecurring(other)) return false
      return (
        other.start_date.slice(0, 10) === event.start_date.slice(0, 10) &&
        sameVenue(event, other) &&
        similarTitle(event.title, other.title)
      )
    })
    if (!duplicate) kept.push(event)
  }
  return kept
}

function suspiciousTime(event: DadEvent) {
  if (!event.time_text) return false
  const context = `${event.title} ${event.description ?? ""}`.toLowerCase()
  if (/overnight|sunrise|dawn|early morning/.test(context)) return false
  if (/\b0[0-5]:[0-5]\d\b/.test(event.time_text)) return true
  const match = event.time_text.match(/\b(1[0-2]|[1-9]):[0-5]\d\s*am\b/i)
  return !!match && Number(match[1]) <= 5
}

function seasonConflict(event: DadEvent) {
  if (!event.start_date) return true
  const month = Number(event.start_date.slice(5, 7))
  const context = `${event.title} ${event.description ?? ""}`.toLowerCase()
  if (context.includes("summer") && [10, 11, 12, 1, 2, 3].includes(month)) return true
  if (/christmas|santa|festive/.test(context) && ![11, 12, 1].includes(month)) return true
  if (/\bnew year\s+20\d{2}\b/.test(context) && ![1, 2].includes(month)) return true
  return false
}

function teenOnly(event: DadEvent) {
  const ages = (event.age_range ?? "").toLowerCase()
  const context = `${event.title} ${ages}`.toLowerCase()
  if (/\bteen(?:ager|agers|s)?\b/.test(context)) return true
  if (/\badults?\s+only\b/.test(context)) return true
  return false
}

/** Hide obviously bad legacy rows without changing Supabase. */
function qualityForDisplay(events: DadEvent[]): DadEvent[] {
  return events
    .filter((event) => !!event.start_date && !seasonConflict(event) && !teenOnly(event))
    .map((event) => (suspiciousTime(event) ? { ...event, time_text: null } : event))
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
      .gte("start_date", today)
      .order("start_date", { ascending: true })
      .order("family_relevance", { ascending: false })
      .limit(MAX_EVENTS)
    if (!error && data?.length) {
      const mapped = data.map((row) => toEvent(row as Record<string, unknown>))
      const clean = dedupeEvents(qualityForDisplay(mapped))
      return { events: geographicallyBalanceEvents(clean), today, saturday, sunday, isSample: false }
    }
  }

  return { events: sampleEvents(saturday, sunday), today, saturday, sunday, isSample: true }
}

export async function fetchEventById(id: string): Promise<DadEvent | null> {
  const db = getSupabase()
  if (!db || !id) return null
  const { data, error } = await db
    .from("collected_events")
    .select("*")
    .eq("id", id)
    .eq("listing_type", "event")
    .limit(1)
    .maybeSingle()
  if (error || !data) return null
  const event = toEvent(data as Record<string, unknown>)
  return qualityForDisplay([event])[0] ?? null
}

export async function fetchSimilarUpcomingEvents(event: DadEvent, limit = 6): Promise<DadEvent[]> {
  const db = getSupabase()
  if (!db) return []
  const today = londonToday()
  const { data, error } = await db
    .from("upcoming_events")
    .select("*")
    .gte("start_date", today)
    .neq("id", event.id)
    .order("start_date", { ascending: true })
    .order("family_relevance", { ascending: false })
    .limit(80)
  if (error || !data) return []

  const mapped = data.map((row) => toEvent(row as Record<string, unknown>))
  const candidates = dedupeEvents(qualityForDisplay(mapped))
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

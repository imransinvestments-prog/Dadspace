import "server-only"
import { getSupabase } from "./supabase"
import { londonHour, londonToday, upcomingWeekend, formatEventDate } from "./dates"
import { sampleArticles, sampleDeal, sampleEvents, sampleThreads } from "./sample-data"
import { distanceKm, geocodeLocations, kmToMiles, locationKey, type Point } from "./geo"
import type { Article, DadEvent, ForumThread, HomeData } from "./types"

const EVENT_COLUMNS =
  "id,title,description,start_date,end_date,time_text,location,event_url,cost_text,age_range,family_relevance,source_url"

function greetingFor(hour: number) {
  if (hour < 5) return "Up with the baby, Dad?"
  if (hour < 12) return "Morning, Dad."
  if (hour < 17) return "Afternoon, Dad."
  if (hour < 21) return "Evening, Dad."
  return "Night shift, Dad?"
}

const NEARBY_RADIUS_MILES = 30
const HOME_EVENT_COUNT = 3

type EventsResult = HomeData["events"]

async function getNearbyEvents(user: Point, saturday: string, sunday: string, today: string): Promise<EventsResult | null> {
  const db = getSupabase()
  if (!db) return null

  const { data, error } = await db
    .from("upcoming_events")
    .select(`${EVENT_COLUMNS},source_id`)
    .gte("end_date", today)
    .order("start_date", { ascending: true })
    .limit(500)
  if (error || !data?.length) return null

  const rows = data as DadEvent[]
  const places = await geocodeLocations(rows)
  const located = rows
    .map((event) => {
      const point = places.get(locationKey(event))
      return point ? { ...event, distance_miles: Math.round(kmToMiles(distanceKm(user, point)) * 10) / 10 } : null
    })
    .filter((e): e is DadEvent & { distance_miles: number } => e !== null)
  if (!located.length) return null

  const byDistance = (a: DadEvent, b: DadEvent) =>
    (a.distance_miles ?? 0) - (b.distance_miles ?? 0) || (b.family_relevance ?? 0) - (a.family_relevance ?? 0)
  const nearby = located.filter((e) => e.distance_miles <= NEARBY_RADIUS_MILES)
  const base = { isSample: false, radiusMiles: NEARBY_RADIUS_MILES }

  const isThisWeekend = (e: DadEvent) => e.start_date <= sunday && (e.end_date ?? e.start_date) >= saturday
  if (nearby.some(isThisWeekend)) {
    // Nearby weekend events come first; any spare slots go to the next-closest weekend events beyond the radius.
    const weekend = located.filter(isThisWeekend).sort(byDistance)
    return { ...base, items: weekend.slice(0, HOME_EVENT_COUNT), isWeekend: true, nearby: "weekend" }
  }
  if (nearby.length) {
    const soon = [...nearby].sort((a, b) => a.start_date.localeCompare(b.start_date) || byDistance(a, b))
    return { ...base, items: soon.slice(0, HOME_EVENT_COUNT), isWeekend: false, nearby: "soon" }
  }
  return { ...base, items: located.sort(byDistance).slice(0, HOME_EVENT_COUNT), isWeekend: false, nearby: "nearest" }
}

async function getWeekendEvents(saturday: string, sunday: string, today: string): Promise<EventsResult> {
  const base = { nearby: null, radiusMiles: NEARBY_RADIUS_MILES }
  const db = getSupabase()
  if (db) {
    const weekend = await db
      .from("upcoming_events")
      .select(EVENT_COLUMNS)
      .lte("start_date", sunday)
      .gte("end_date", saturday)
      .order("family_relevance", { ascending: false })
      .order("start_date", { ascending: true })
      .limit(3)
    if (!weekend.error && weekend.data?.length) {
      return { ...base, items: weekend.data as DadEvent[], isSample: false, isWeekend: true }
    }

    const upcoming = await db
      .from("upcoming_events")
      .select(EVENT_COLUMNS)
      .gte("end_date", today)
      .order("start_date", { ascending: true })
      .order("family_relevance", { ascending: false })
      .limit(3)
    if (!upcoming.error && upcoming.data?.length) {
      return { ...base, items: upcoming.data as DadEvent[], isSample: false, isWeekend: false }
    }
  }
  return { ...base, items: sampleEvents(saturday, sunday), isSample: true, isWeekend: true }
}

function commentCount(value: unknown): number {
  if (typeof value === "number") return value
  if (Array.isArray(value)) return value.length
  if (typeof value === "string" && !Number.isNaN(Number(value))) return Number(value)
  return 0
}

async function getTrendingThreads() {
  const db = getSupabase()
  if (db) {
    const { data, error } = await db.from("forum_threads").select("*").limit(50)
    if (!error && data?.length) {
      const items: ForumThread[] = data
        .map((row) => ({
          id: String(row.id),
          title: String(row.title ?? "Untitled thread"),
          category: row.category ?? null,
          author: row.author ?? null,
          comments: commentCount(row.comments),
        }))
        .sort((a, b) => b.comments - a.comments)
        .slice(0, 5)
      return { items, isSample: false }
    }
  }
  return { items: sampleThreads, isSample: true }
}

const HEADLINE_CATEGORIES = ["activities", "money", "safety", "policy"]
const HEADLINE_COUNT = 4

async function getLatestArticles() {
  const db = getSupabase()
  if (db) {
    const { data, error } = await db
      .from("feed_items")
      .select("id,title,url,source_name,category,published_at")
      .not("category", "is", null)
      .order("published_at", { ascending: false, nullsFirst: false })
      .limit(300)
    if (!error && data?.length) {
      const newestByCategory = new Map<string, (typeof data)[number]>()
      for (const row of data) {
        if (!newestByCategory.has(row.category)) newestByCategory.set(row.category, row)
      }
      // Preferred categories first, then the freshest remaining categories fill any gaps.
      const chosen = [
        ...HEADLINE_CATEGORIES.filter((c) => newestByCategory.has(c)),
        ...[...newestByCategory.keys()].filter((c) => !HEADLINE_CATEGORIES.includes(c)),
      ].slice(0, HEADLINE_COUNT)
      const items: Article[] = chosen.map((category) => {
        const row = newestByCategory.get(category)!
        return { id: String(row.id), title: row.title, source: row.source_name, url: row.url, category }
      })
      if (items.length) return { items, isSample: false }
    }
  }
  return { items: sampleArticles, isSample: true }
}

async function getEvents(user: Point | null, saturday: string, sunday: string, today: string) {
  if (user) {
    try {
      const nearby = await getNearbyEvents(user, saturday, sunday, today)
      if (nearby) return nearby
    } catch {
      // Fall through to the unsorted list if geocoding is unavailable.
    }
  }
  return getWeekendEvents(saturday, sunday, today)
}

export async function getHomeData(user: Point | null = null): Promise<HomeData> {
  const today = londonToday()
  const { saturday, sunday, sleeps } = upcomingWeekend(today)

  const [events, threads, articles] = await Promise.all([
    getEvents(user, saturday, sunday, today),
    getTrendingThreads(),
    getLatestArticles(),
  ])

  return {
    greeting: greetingFor(londonHour()),
    sleepsToWeekend: sleeps,
    weekendLabel: formatEventDate(saturday, sunday),
    events,
    threads,
    articles,
    // No deals table exists yet, so the top deal is always sample content.
    deal: { items: sampleDeal, isSample: true },
  }
}

import "server-only"
import { getSupabase } from "./supabase"
import { londonHour, londonToday, upcomingWeekend, formatEventDate } from "./dates"
import { sampleArticles, sampleDeal, sampleEvents, sampleThreads } from "./sample-data"
import type { Article, DadEvent, ForumThread, HomeData, NewsItem, NewsPageData, NewsSource } from "./types"

const EVENT_COLUMNS =
  "id,title,description,start_date,end_date,time_text,location,event_url,cost_text,age_range,family_relevance,source_url"

function greetingFor(hour: number) {
  if (hour < 5) return "Up with the baby, Dad?"
  if (hour < 12) return "Morning, Dad."
  if (hour < 17) return "Afternoon, Dad."
  if (hour < 21) return "Evening, Dad."
  return "Night shift, Dad?"
}

async function getWeekendEvents(saturday: string, sunday: string, today: string) {
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
      return { items: weekend.data as DadEvent[], isSample: false, isWeekend: true }
    }

    const upcoming = await db
      .from("upcoming_events")
      .select(EVENT_COLUMNS)
      .gte("end_date", today)
      .order("start_date", { ascending: true })
      .order("family_relevance", { ascending: false })
      .limit(3)
    if (!upcoming.error && upcoming.data?.length) {
      return { items: upcoming.data as DadEvent[], isSample: false, isWeekend: false }
    }
  }
  return { items: sampleEvents(saturday, sunday), isSample: true, isWeekend: true }
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

async function getLatestArticles() {
  const db = getSupabase()
  if (db) {
    const { data, error } = await db.from("articles").select("id,title,source").order("id", { ascending: false }).limit(4)
    if (!error && data?.length) {
      return { items: data.map((a) => ({ ...a, id: String(a.id) })) as Article[], isSample: false }
    }
  }
  return { items: sampleArticles, isSample: true }
}

const NEWS_COLUMNS = "id,title,url,source_name,published_at,summary,why_it_matters,category,relevance"

async function queryNews(table: "feed_items" | "news_items", category: string | null) {
  const db = getSupabase()
  if (!db) return null
  let query = db
    .from(table)
    .select(NEWS_COLUMNS)
    .order("published_at", { ascending: false, nullsFirst: false })
    .limit(60)
  if (category) query = query.eq("category", category)
  const { data, error } = await query
  if (error) return null
  return (data ?? []).map((row) => ({ ...row, id: String(row.id) })) as NewsItem[]
}

export async function getNewsPageData(requestedCategory?: string): Promise<NewsPageData> {
  const db = getSupabase()
  const sourcesResult = db
    ? await db.from("news_sources").select("name,category").eq("active", true).order("name")
    : null
  const sources = (sourcesResult?.data ?? []) as NewsSource[]
  const categories = [...new Set(sources.map((s) => s.category).filter((c): c is string => Boolean(c)))].sort()

  const activeCategory = requestedCategory && categories.includes(requestedCategory) ? requestedCategory : null
  const items = (await queryNews("feed_items", activeCategory)) ?? (await queryNews("news_items", activeCategory)) ?? []

  return { items, sources, categories, activeCategory }
}

export async function getHomeData(): Promise<HomeData> {
  const today = londonToday()
  const { saturday, sunday, sleeps } = upcomingWeekend(today)

  const [events, threads, articles] = await Promise.all([
    getWeekendEvents(saturday, sunday, today),
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

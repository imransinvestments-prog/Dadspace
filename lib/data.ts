import "server-only"
import { getMonthlyNews } from "./news-monthly"
import { getSupabase } from "./supabase"
import { FORUM_ENABLED } from "./launch"
import { londonHour, londonToday, upcomingWeekend, formatEventDate } from "./dates"
import type { ForumThread, HomeData } from "./types"

function greetingFor(hour: number) {
  if (hour < 5) return "Up with the baby, Dad?"
  if (hour < 12) return "Morning, Dad."
  if (hour < 17) return "Afternoon, Dad."
  if (hour < 21) return "Evening, Dad."
  return "Night shift, Dad?"
}

function commentCount(value: unknown): number {
  if (typeof value === "number") return value
  if (Array.isArray(value)) return value.length
  if (typeof value === "string" && !Number.isNaN(Number(value))) return Number(value)
  return 0
}

async function getTrendingThreads() {
  // The section is hidden until launch, so skip the query rather than discard its rows.
  if (!FORUM_ENABLED) return { items: [], isSample: false }
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
  return { items: [], isSample: false }
}

// Deals, places and nearby listings load through their own sources, so this only
// assembles the sections the dashboard renders from it.
export async function getHomeData(): Promise<HomeData> {
  const { saturday, sunday, sleeps } = upcomingWeekend(londonToday())
  const [threads, monthlyNews] = await Promise.all([getTrendingThreads(), getMonthlyNews()])

  return {
    greeting: greetingFor(londonHour()),
    sleepsToWeekend: sleeps,
    weekendLabel: formatEventDate(saturday, sunday),
    threads,
    monthlyNews,
  }
}

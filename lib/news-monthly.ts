import "server-only"
import { unstable_cache } from "next/cache"
import { getSupabase } from "./supabase"
import { CATEGORIES } from "./news"
import { newsMonth } from "./news-month"

const readMonthlyNews = unstable_cache(async (month: ReturnType<typeof newsMonth>) => {
  const unavailable = { month: month.label, counts: null }
  // news_items is private: anon RLS would return misleading zero counts.
  if (!process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY) return unavailable
  const db = getSupabase()
  if (!db) return unavailable
  try {
    const results = await Promise.all(CATEGORIES.filter(c => c.value !== "all").map(async category => {
      const { count, error } = await db.from("news_items").select("id", { count: "exact", head: true })
        .eq("category", category.value).gte("created_at", month.start).lt("created_at", month.end)
        .gte("relevance", 3).or("is_primary.eq.true,is_primary.is.null")
      if (error || count === null) throw new Error("Monthly news unavailable")
      return [category.value, count] as const
    }))
    return { month: month.label, counts: Object.fromEntries(results) }
  } catch {
    return unavailable
  }
}, ["home-monthly-news"], { revalidate: 600 })

export async function getMonthlyNews() {
  return readMonthlyNews(newsMonth())
}

import "server-only"
import { getSupabase } from "./supabase"
import { selectDeals, type LiveDeal } from "./deals-selection"

export async function getDeals(): Promise<{ items: LiveDeal[]; loadFailed: boolean }> {
  const db = getSupabase()
  if (!db) return { items: [], loadFailed: true }
  try {
    const { data, error } = await db.from("deals")
      .select("id,title,description,retailer,price,was_price,discount_pct,image_url,display_group,matched_item,link,posted_at,last_seen,expires_at,relevance,audience_evidence,classified_by,status")
      .eq("status", "live")
      .like("classified_by", "quality-v1:source-%")
      .gte("last_seen", new Date(Date.now() - 72 * 3600000).toISOString())
      .order("last_seen", { ascending: false }).limit(1000)
    return error ? { items: [], loadFailed: true } : { items: selectDeals((data ?? []) as LiveDeal[]), loadFailed: false }
  } catch { return { items: [], loadFailed: true } }
}


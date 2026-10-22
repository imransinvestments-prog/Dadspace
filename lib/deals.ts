import "server-only"
import { getSupabase } from "./supabase"
import { eligibleDeal, selectDeals, type LiveDeal } from "./deals-selection"
import { cache } from "react"
import { unstable_cache } from "next/cache"

// Deals change only when the collector runs, so the selected feed is shared across
// requests for a few minutes instead of re-reading up to 1000 rows per page view.
const DEALS_REVALIDATE_SECONDS = 300

// Throws on failure so an unavailable read is retried next request rather than cached.
const readSelectedDeals = unstable_cache(async (): Promise<LiveDeal[]> => {
  const db = getSupabase()
  if (!db) throw new Error("Deals unavailable")
  const { data, error } = await db.from("deals")
    .select("id,title,description,retailer,price,was_price,discount_pct,image_url,display_group,matched_item,item_id,source_id,value_band,link,posted_at,last_seen,expires_at,relevance,audience_evidence,classified_by,status,taxonomy:parent_discount_items!deals_item_id_fkey!inner(id,active,display_group,equivalent_item_id,deal_type)")
    .eq("status", "live")
    .eq("taxonomy.active", true)
    .like("classified_by", "quality-v1:source-%")
    .gte("last_seen", new Date(Date.now() - 72 * 3600000).toISOString())
    .order("last_seen", { ascending: false }).limit(1000)
  if (error || !Array.isArray(data)) throw new Error("Deals unavailable")
  const rows = (data ?? []).map(row => {
    const taxonomy = row.taxonomy as unknown as {display_group: string; equivalent_item_id: number | null; deal_type: string}
    return { ...row, display_group: taxonomy.display_group, equivalent_item_id: taxonomy.equivalent_item_id, deal_type: taxonomy.deal_type }
  })
  return selectDeals(rows as LiveDeal[])
}, ["public-selected-deals"], { revalidate: DEALS_REVALIDATE_SECONDS, tags: ["deals"] })

export const getDeals = cache(async (): Promise<{ items: LiveDeal[]; loadFailed: boolean }> => {
  try {
    // Re-check eligibility so an offer that expires or ages out within the cache window is not shown.
    const now = Date.now()
    return { items: (await readSelectedDeals()).filter(deal => eligibleDeal(deal, now)), loadFailed: false }
  } catch { return { items: [], loadFailed: true } }
})

const readDealGroups = unstable_cache(async (): Promise<string[]> => {
  const db = getSupabase()
  if (!db) throw new Error("Deal groups unavailable")
  const { data, error } = await db.from("parent_discount_items").select("display_group").eq("active", true).not("display_group", "is", null).limit(1000)
  if (error) throw new Error("Deal groups unavailable")
  return [...new Set((data ?? []).map(row => row.display_group as string))].sort()
}, ["public-deal-groups"], { revalidate: DEALS_REVALIDATE_SECONDS, tags: ["deals"] })

export async function getDealGroups(): Promise<string[]> {
  try { return await readDealGroups() } catch { return [] }
}

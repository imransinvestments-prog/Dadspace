import "server-only"
import { getSupabase } from "./supabase"
import { selectDeals, type LiveDeal } from "./deals-selection"

export async function getDeals(): Promise<{ items: LiveDeal[]; loadFailed: boolean }> {
  const db = getSupabase()
  if (!db) return { items: [], loadFailed: true }
  try {
    const { data, error } = await db.from("deals")
      .select("id,title,description,retailer,price,was_price,discount_pct,image_url,display_group,matched_item,item_id,source_id,value_band,link,posted_at,last_seen,expires_at,relevance,audience_evidence,classified_by,status,taxonomy:parent_discount_items!deals_item_id_fkey!inner(id,active,display_group,equivalent_item_id,deal_type)")
      .eq("status", "live")
      .eq("taxonomy.active", true)
      .like("classified_by", "quality-v1:source-%")
      .gte("last_seen", new Date(Date.now() - 72 * 3600000).toISOString())
      .order("last_seen", { ascending: false }).limit(1000)
    if (error) return { items: [], loadFailed: true }
    const rows = (data ?? []).map(row => {
      const taxonomy = row.taxonomy as unknown as {display_group: string; equivalent_item_id: number | null; deal_type: string}
      return { ...row, display_group: taxonomy.display_group, equivalent_item_id: taxonomy.equivalent_item_id, deal_type: taxonomy.deal_type }
    })
    return { items: selectDeals(rows as LiveDeal[]), loadFailed: false }
  } catch { return { items: [], loadFailed: true } }
}

export async function getDealGroups(): Promise<string[]> {
  const db = getSupabase()
  if (!db) return []
  const { data, error } = await db.from("parent_discount_items").select("display_group").eq("active", true).not("display_group", "is", null).limit(1000)
  return error ? [] : [...new Set((data ?? []).map(row => row.display_group as string))].sort()
}


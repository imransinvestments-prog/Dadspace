import "server-only"
import { cache } from "react"
import { getSupabase } from "./supabase"
import { toVenue } from "./venues"
import type { Venue } from "./venue-meta"

// Explicit projection: never send internal notes, review evidence or imported JSON to clients.
export const VENUE_PUBLIC_COLUMNS = "id,venue_name,venue_label,category,address,address_line_1,address_line_2,town_city,postcode,country,nearby_settlement,latitude,longitude,website,fee,opening_hours,image_url,image_source_url,image_attribution,image_license,image_license_url,image_title,image_credit"
export type VenuePage = { venues: Venue[]; total: number; hasMore: boolean; loadFailed: boolean }
export const PILOT_AREAS = [
  { slug: "hounslow", name: "Hounslow", intro: "Browse Hounslow libraries for your next family visit. Check the library's own website for current opening times and children's sessions." },
  { slug: "manchester", name: "Manchester", intro: "Explore Manchester museums and libraries. Compare addresses and available visitor information before planning a day with the kids." },
  { slug: "london", name: "London", intro: "Find London museums, libraries and indoor play venues. London covers a large area: check the address and journey before choosing your next stop." },
] as const
export const DISCOVERY_CATEGORIES = [
  { slug: "libraries", name: "Libraries", raw: "library", image: "/images/event-story.png" },
  { slug: "museums", name: "Museums", raw: "Museum", image: "/images/venues/museum.png" },
  { slug: "soft-play", name: "Soft play", raw: "Indoor / soft play centre", image: "/images/venues/soft-play.png" },
] as const

export function discoveryArea(slug: string) { return PILOT_AREAS.find(a => a.slug === slug) }
export function discoveryCategory(slug: string) { return DISCOVERY_CATEGORIES.find(c => c.slug === slug) }
const empty = (loadFailed: boolean): VenuePage => ({ venues: [], total: 0, hasMore: false, loadFailed })

const readPublicPage = cache(async (page: number, town?: string, category?: string): Promise<VenuePage> => {
  const db = getSupabase()
  if (!db) return empty(true)
  const offset = (page - 1) * 24
  let query = db.from("venues").select(VENUE_PUBLIC_COLUMNS, { count: "exact" }).eq("public_visible", true)
  if (town) query = query.eq("town_city", town)
  if (category) query = query.eq("category", category)
  const { data, error, count } = await query.order("venue_name").order("id").range(offset, offset + 23)
  if (error) return empty(true)
  const venues = (data ?? []).map(toVenue).filter((v): v is Venue => v !== null)
  return { venues, total: count ?? 0, hasMore: offset + (data?.length ?? 0) < (count ?? 0), loadFailed: false }
})
export function publicVenuePage({page = 1, town, category}: {page?: number; town?: string; category?: string} = {}) {
  return readPublicPage(page, town, category)
}

export const publicVenueById = cache(async (id: string): Promise<Venue | null> => {
  const db = getSupabase()
  if (!db) throw new Error("Venue information is temporarily unavailable")
  const { data, error } = await db.from("venues").select(VENUE_PUBLIC_COLUMNS).eq("public_visible", true).eq("id", id).maybeSingle()
  if (error) throw new Error("Venue information is temporarily unavailable")
  return data ? toVenue(data) : null
})

export async function approvedDiscoveryPages() {
  const combinations = PILOT_AREAS.flatMap(area => DISCOVERY_CATEGORIES.map(category => ({ area, category })))
  const results = await Promise.all(combinations.map(async pair => ({ ...pair, result: await publicVenuePage({ town: pair.area.name, category: pair.category.raw }) })))
  // No synthetic pages to fill a coverage quota. Below-threshold supply stays unindexed.
  return results.filter(p => !p.result.loadFailed && p.result.total >= 3)
}

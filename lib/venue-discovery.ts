import "server-only"
import { cache } from "react"
import { unstable_cache } from "next/cache"
import { getSupabase } from "./supabase"
import { toVenue } from "./venues"
import type { Venue } from "./venue-meta"
import { createHash } from "node:crypto"
import { DISCOVERY_APPROVALS, discoveryPublicationReady } from "./discovery-publication"

// Explicit projection: never send internal notes, review evidence or imported JSON to clients.
export const VENUE_PUBLIC_COLUMNS = "id,venue_name,venue_label,category,address,address_line_1,address_line_2,town_city,postcode,country,nearby_settlement,latitude,longitude,website,fee,opening_hours,access,image_url,image_source_url,image_attribution,image_license,image_license_url,image_title,image_credit"
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

// An exact count scans every visible venue, so the display total is shared for
// five minutes. Rows and hasMore always come from a fresh read, so revocation
// still takes effect immediately. Failures throw and are never cached.
const readPublicTotal = unstable_cache(async (town?: string, category?: string): Promise<number> => {
  const db = getSupabase()
  if (!db) throw new Error("Venue information is temporarily unavailable")
  let query = db.from("venues").select("id", { count: "exact", head: true }).eq("public_visible", true)
  if (town) query = query.eq("town_city", town)
  if (category) query = query.eq("category", category)
  const { count, error } = await query
  if (error || !Number.isSafeInteger(count) || count! < 0) throw new Error("Venue total unavailable")
  return count!
}, ["public-venue-total-v1"], { revalidate: 300 })

const readPublicPage = cache(async (page: number, town?: string, category?: string): Promise<VenuePage> => {
  try {
  const db = getSupabase()
  if (!db) return empty(true)
  const offset = (page - 1) * 24
  let query = db.from("venues").select(VENUE_PUBLIC_COLUMNS).eq("public_visible", true)
  if (town) query = query.eq("town_city", town)
  if (category) query = query.eq("category", category)
  // One row beyond the page proves whether another page exists without a fresh count.
  const [{ data, error }, recentTotal] = await Promise.all([query.order("venue_name").order("id").range(offset, offset + 24), readPublicTotal(town, category)])
  if (error || !Array.isArray(data)) return empty(true)
  const hasMore = data.length > 24, rows = data.slice(0, 24)
  // An empty page that the recent total says should hold venues is a failed read, not empty supply.
  if (!rows.length && recentTotal > offset) return empty(true)
  const venues = rows.map(toVenue).filter((v): v is Venue => v !== null)
  return { venues, total: hasMore ? Math.max(recentTotal, offset + rows.length + 1) : offset + rows.length, hasMore, loadFailed: false }
  } catch { return empty(true) }
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
  const combinations = PILOT_AREAS.flatMap(area => DISCOVERY_CATEGORIES.filter(category => DISCOVERY_APPROVALS.some(a=>a.area===area.slug && a.category===category.slug)).map(category => ({ area, category })))
  const results = await Promise.all(combinations.map(async pair => ({ ...pair, result: await publicVenuePage({ town: pair.area.name, category: pair.category.raw }) })))
  // No synthetic pages to fill a coverage quota. Below-threshold supply stays unindexed.
  const checked=await Promise.all(results.map(async p=>({...p, approved: await discoveryPageApproved(p.area.slug,p.category.slug)})))
  return checked.filter(p=>p.approved)
}

export const discoveryPageApproved=cache(async (areaSlug: string, categorySlug: string) => {
 const area=discoveryArea(areaSlug), category=discoveryCategory(categorySlug)
 if (!area || !category || !DISCOVERY_APPROVALS.some(a=>a.area===areaSlug && a.category===categorySlug)) return false
 // Bounded complete cohort: large areas require a separate publication design.
 const rows: {id:string;fingerprint:string}[]=[]
 let total=0
 for (let page=1;page<=5;page++) {
  const result=await publicVenuePage({town:area.name,category:category.raw,page})
  if (result.loadFailed || result.total>120 || (page>1 && total!==result.total)) return false
  total=result.total
  rows.push(...result.venues.map(v=>({id:v.id,fingerprint:createHash('sha256').update(JSON.stringify(v)).digest('hex')})))
  if (!result.hasMore) return discoveryPublicationReady(areaSlug,categorySlug,rows,total,false)
 }
 return false
})

// Follow only explicit reviewed aliases. Never infer identity from names/postcodes.
export const publicVenueDestination = cache(async (id: string): Promise<Venue | null> => {
  const db = getSupabase()
  if (!db) throw new Error("Venue information is temporarily unavailable")
  const seen = new Set<string>()
  for (let hop = 0; hop < 8; hop++) {
    if (seen.has(id)) return null
    seen.add(id)
    const { data, error } = await db.from("venues").select("id,merged_into,public_visible").eq("id", id).maybeSingle()
    if (error) throw new Error("Venue information is temporarily unavailable")
    if (!data) return null
    if (data.merged_into) { id = data.merged_into; continue }
    return data.public_visible === true ? publicVenueById(id) : null
  }
  return null
})

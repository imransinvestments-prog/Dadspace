import { getSupabase } from "@/lib/supabase"
import { toVenue } from "@/lib/venues"
import { parsePoint } from "@/lib/distance"
import { milesBetween, type Venue } from "@/lib/venue-meta"
import { interleavePlaces } from "@/lib/local-places"

export const dynamic = "force-dynamic"
export const maxDuration = 60

export async function GET(request: Request) {
  const params = new URL(request.url).searchParams
  const validated = parsePoint(params)
  if (!validated) return Response.json({ error: "A valid location is required." }, { status: 400 })
  // Preserve the supplied postcode centre after validation. Production device
  // coordinates are already approximated by the location provider.
  const point = { lat: Number(params.get("lat")), lng: Number(params.get("lng")) }
  const db = getSupabase()
  if (!db) return Response.json({ error: "Local places are unavailable." }, { status: 503 })
  try {
    const { data: counts, error } = await db.rpc("venue_category_counts")
    if (error || !Array.isArray(counts)) throw new Error("Category lookup failed")
    const categories = counts.filter((c: {key: string; count: number}) => c.key && Number(c.count) > 0)
    const groups: Venue[][] = []
    // Bound concurrent calls while using the directory's existing indexed nearby query.
    for (let start = 0; start < categories.length; start += 4) {
      const batch = await Promise.all(categories.slice(start, start + 4).map(async (category: {key: string}) => {
        const { data, error } = await db.rpc("nearby_venue_page", {
          p_lat: point.lat, p_lng: point.lng, p_query: "", p_category: category.key,
          p_free: false, p_indoor: false, p_outdoor: false, p_offset: 0, p_limit: 6,
        })
        if (error || !data || !Array.isArray(data.rows)) throw new Error("Nearby lookup failed")
        return data.rows.map((row: Record<string, unknown>) => toVenue(row))
          .filter((v: Venue | null): v is Venue => !!v && v.latitude != null && v.longitude != null)
          .sort((a: Venue, b: Venue) =>
            milesBetween(point, {lat: a.latitude!, lng: a.longitude!}) - milesBetween(point, {lat: b.latitude!, lng: b.longitude!})
            || a.id.localeCompare(b.id))
      }))
      groups.push(...batch)
    }
    return Response.json({ venues: interleavePlaces(groups) }, { headers: { "Cache-Control": "private, no-store" } })
  } catch {
    return Response.json({ error: "Local places are unavailable. Please try again." }, { status: 503 })
  }
}

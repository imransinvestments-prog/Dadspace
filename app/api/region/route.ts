import { NextResponse } from "next/server"
import { parsePoint } from "@/lib/distance"
import { NEWS_LOCATION_VERSION, newsArea, newsGeoRegion } from "@/lib/news-geography"

const COUNTRY_TO_REGION: Record<string, string> = {
  England: "england",
  Scotland: "scotland",
  Wales: "wales",
  "Northern Ireland": "northern_ireland",
}

type PostcodeResult = {
  country: string
  region?: string | null
  admin_district?: string | null
  admin_county?: string | null
  parish?: string | null
  admin_ward?: string | null
}

type PostcodesResponse = { result: PostcodeResult[] | null }

/**
 * Turns coordinates into a coarse UK news location using postcodes.io (free, no key).
 * Coordinates are rounded to ~1km before leaving the server and are never stored.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const point = parsePoint(searchParams)
  if (!point) {
    return NextResponse.json({ error: "invalid_coordinates" }, { status: 400 })
  }

  const url = new URL("https://api.postcodes.io/postcodes")
  url.searchParams.set("lat", point.lat.toFixed(2))
  url.searchParams.set("lon", point.lng.toFixed(2))
  url.searchParams.set("radius", "2000")
  url.searchParams.set("limit", "1")

  try {
    const res = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(8000) })
    if (!res.ok) return NextResponse.json({ region: null })
    const body = (await res.json()) as PostcodesResponse
    const place = body.result?.[0]
    if (!place) return NextResponse.json({ region: null })

    return NextResponse.json({
      version: NEWS_LOCATION_VERSION,
      region: COUNTRY_TO_REGION[place.country] ?? null,
      geoRegion: place.country === "England" ? newsGeoRegion(place.region) : null,
      adminArea: newsArea(place.admin_county) ?? newsArea(place.admin_district),
      // Match the worker's council district, never a parish or electoral ward.
      locality: newsArea(place.admin_district),
    })
  } catch {
    return NextResponse.json({ error: "lookup_failed" }, { status: 502 })
  }
}

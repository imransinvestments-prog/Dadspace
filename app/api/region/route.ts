import { NextResponse } from "next/server"

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

function slug(value?: string | null) {
  if (!value) return null
  const cleaned = value
    .trim()
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
  return cleaned || null
}

/**
 * Turns coordinates into a coarse UK news location using postcodes.io (free, no key).
 * Coordinates are rounded to ~1km before leaving the server and are never stored.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const lat = Number(searchParams.get("lat"))
  const lng = Number(searchParams.get("lng"))

  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) {
    return NextResponse.json({ error: "invalid_coordinates" }, { status: 400 })
  }

  const url = new URL("https://api.postcodes.io/postcodes")
  url.searchParams.set("lat", lat.toFixed(2))
  url.searchParams.set("lon", lng.toFixed(2))
  url.searchParams.set("radius", "2000")
  url.searchParams.set("limit", "1")

  try {
    const res = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(8000) })
    if (!res.ok) return NextResponse.json({ region: null })
    const body = (await res.json()) as PostcodesResponse
    const place = body.result?.[0]
    if (!place) return NextResponse.json({ region: null })

    return NextResponse.json({
      region: COUNTRY_TO_REGION[place.country] ?? null,
      geoRegion: slug(place.region),
      adminArea: slug(place.admin_district ?? place.admin_county),
      locality: slug(place.parish ?? place.admin_ward ?? place.admin_district),
    })
  } catch {
    return NextResponse.json({ error: "lookup_failed" }, { status: 502 })
  }
}

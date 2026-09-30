import { NextResponse } from "next/server"

const COUNTRY_TO_REGION: Record<string, string> = {
  England: "england",
  Scotland: "scotland",
  Wales: "wales",
  "Northern Ireland": "northern_ireland",
}

type PostcodesResponse = { result: { country: string }[] | null }

/**
 * Turns a phone's coordinates into a UK nation using postcodes.io (free, no key).
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
    const country = body.result?.[0]?.country
    return NextResponse.json({ region: (country && COUNTRY_TO_REGION[country]) ?? null })
  } catch {
    return NextResponse.json({ error: "lookup_failed" }, { status: 502 })
  }
}

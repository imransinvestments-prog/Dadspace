import { NextRequest, NextResponse } from "next/server"
import { parsePoint } from "@/lib/distance"
import { forecastDays, weatherConfigured } from "@/lib/weather"
export const dynamic = "force-dynamic"

// Responses depend on the visitor's location or IP, so they are never shared.
const respond = (body: object, status = 200) => NextResponse.json(body, { status, headers: { "Cache-Control": "private, no-store" } })

export async function GET(request: NextRequest) {
  if (!weatherConfigured()) return respond({ status: "not_configured" })
  const params = request.nextUrl.searchParams
  let point = parsePoint(params), approximate = false, area: string | null = null
  if (!point && (params.has("lat") || params.has("lng"))) return respond({ error: "Invalid location" }, 400)
  if (!point) {
    // No chosen location: Vercel's IP geolocation gives a rough area. Neither the
    // address nor the coordinates are stored or logged.
    const lat = request.headers.get("x-vercel-ip-latitude"), lng = request.headers.get("x-vercel-ip-longitude")
    point = lat && lng ? parsePoint(new URLSearchParams({ lat, lng })) : null
    if (!point) return respond({ status: "no_location" })
    approximate = true
    try { area = decodeURIComponent(request.headers.get("x-vercel-ip-city") || "") || null } catch { area = null }
  }
  try {
    const days = await forecastDays(point)
    if (!days.length) return respond({ status: "unavailable" }, 503)
    return respond({ status: "ok", approximate, area, days })
  } catch {
    return respond({ status: "unavailable" }, 503)
  }
}

import { NextRequest, NextResponse } from "next/server"
import { parsePoint } from "@/lib/distance"
import { forecastDays, weatherConfigured } from "@/lib/weather"
export const dynamic = "force-dynamic"

// Responses depend on the visitor's location or IP, so they are never shared.
const respond = (body: object, status = 200) => NextResponse.json(body, { status, headers: { "Cache-Control": "private, no-store" } })

// A short code for why a forecast failed, safe to log and return: never the key, the
// coordinates or the provider's own message.
function failureReason(error: unknown) {
  const { name = "", message = "" } = (error ?? {}) as { name?: string; message?: string }
  const http = String(message).match(/^Met Office HTTP (\d{3})$/)
  if (http) return `upstream_${http[1]}`
  if (name === "TimeoutError" || name === "AbortError") return "timeout"
  if (message === "Unexpected Met Office response" || name === "SyntaxError") return "bad_response"
  return "error"
}

function unavailable(reason: string) {
  console.error(`[weather] forecast unavailable: ${reason}`)
  return respond({ status: "unavailable", reason }, 503)
}

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
    if (!days.length) return unavailable("no_days")
    return respond({ status: "ok", approximate, area, days })
  } catch (error) {
    return unavailable(failureReason(error))
  }
}

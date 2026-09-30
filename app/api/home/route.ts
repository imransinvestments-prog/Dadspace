import { getHomeData } from "@/lib/data"
import type { Point } from "@/lib/geo"

export const dynamic = "force-dynamic"

function parsePoint(searchParams: URLSearchParams): Point | null {
  const lat = Number(searchParams.get("lat"))
  const lng = Number(searchParams.get("lng"))
  if (!searchParams.has("lat") || !searchParams.has("lng")) return null
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) return null
  // Coordinates are only used to sort events for this response and are never stored.
  return { lat: Math.round(lat * 100) / 100, lng: Math.round(lng * 100) / 100 }
}

export async function GET(request: Request) {
  const data = await getHomeData(parsePoint(new URL(request.url).searchParams))
  return Response.json(data, { headers: { "Cache-Control": "no-store" } })
}

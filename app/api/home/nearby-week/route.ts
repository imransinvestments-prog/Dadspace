import { NextRequest, NextResponse } from "next/server"
import { parsePoint } from "@/lib/distance"
import { fetchUpcomingEvents } from "@/lib/events"
import { distanceKm, kmToMiles } from "@/lib/geo"
import { londonToday, weekday, addDays } from "@/lib/dates"
import { weekActivityPoints } from "@/lib/home-nearby"
export const dynamic = "force-dynamic"
export const maxDuration = 60
export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams
  if (!parsePoint(params)) return NextResponse.json({error:"Location required"},{status:400})
  const point = {lat:Number(params.get("lat")),lng:Number(params.get("lng"))}
  const today = londonToday(), weekStart = addDays(today,-((weekday(today)+6)%7)), weekEnd = addDays(weekStart,6)
  const [eventsResult,countResult] = await Promise.allSettled([
    fetchUpcomingEvents(point, 30 * 1.609344).then(result => {
      if (result.loadFailed) throw new Error("Events unavailable")
      return result.isSample ? [] : result.events.filter(e => {
        if ((e.end_date ?? e.start_date) < today || e.distance_miles == null) return false
        // fetchUpcomingEvents already applies the shared occurrence rule.
        return true
      }).slice(0,2)
    }),
    weekActivityPoints(weekStart,weekEnd).then(points =>
      new Set(points.filter(row => kmToMiles(distanceKm(point,row)) <= 30).map(row => row.id)).size),
  ])
  return NextResponse.json({events:eventsResult.status === "fulfilled" ? eventsResult.value : [],eventsUnavailable:eventsResult.status === "rejected",activityCount:countResult.status === "fulfilled" ? countResult.value : null,weekStart,weekEnd,radiusMiles:30}, {headers:{"Cache-Control":"private, no-store"}})
}

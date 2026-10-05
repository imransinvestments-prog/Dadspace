import { NextRequest, NextResponse } from "next/server"
import { getSupabase } from "@/lib/supabase"
import { parsePoint } from "@/lib/distance"
import { fetchUpcomingEvents } from "@/lib/events"
import { withDistances } from "@/lib/listing-distance"
import { londonToday, weekday, addDays } from "@/lib/dates"
import { activeThisWeek } from "@/lib/home-selection"
export const dynamic = "force-dynamic"
export const maxDuration = 60
export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams
  if (!parsePoint(params)) return NextResponse.json({error:"Location required"},{status:400})
  const point = {lat:Number(params.get("lat")),lng:Number(params.get("lng"))}
  const today = londonToday(), weekStart = addDays(today,-((weekday(today)+6)%7)), weekEnd = addDays(weekStart,6)
  const [eventsResult,countResult] = await Promise.allSettled([
    fetchUpcomingEvents(point).then(result => result.isSample ? [] : result.events.filter(e => (e.end_date ?? e.start_date) >= today && e.distance_miles != null).slice(0,2)),
    (async () => {
      const db = getSupabase()
      if (!db) throw new Error("Activities unavailable")
      const rows: {id:string;location:string|null;postcode:string|null;venue_id:string|null;source_id:string|null;start_date:string|null;end_date:string|null;recurrence:string|null}[] = []
      for(let offset=0;;offset+=500) {
        const {data,error} = await db.from("current_activities").select("id,location,postcode,venue_id,source_id,start_date,end_date,recurrence").order("id").range(offset,offset+499)
        if(error) throw error
        rows.push(...(data ?? []))
        if((data?.length ?? 0)<500) break
      }
      const located = await withDistances(rows.filter(row => activeThisWeek(row,weekStart,weekEnd)),point)
      return new Set(located.filter(row => row.distance_miles != null && row.distance_miles <= 30).map(row => row.id)).size
    })()
  ])
  return NextResponse.json({events:eventsResult.status === "fulfilled" ? eventsResult.value : [],eventsUnavailable:eventsResult.status === "rejected",activityCount:countResult.status === "fulfilled" ? countResult.value : null,weekStart,weekEnd,radiusMiles:30})
}

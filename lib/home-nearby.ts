import "server-only"
import { unstable_cache } from "next/cache"
import { getSupabase } from "./supabase"
import { listingPoints } from "./listing-distance"
import { activeThisWeek } from "./home-selection"
import type { Point } from "./distance"

type ActivityRow = {id:string;location:string|null;postcode:string|null;venue_id:string|null;source_id:string|null;start_date:string|null;end_date:string|null;recurrence:string|null}

/**
 * Where this week's activities are, independent of the visitor, so each request only measures distances.
 * Activities that cannot be located are omitted, as they were never within the radius count.
 */
export const weekActivityPoints = unstable_cache(async (weekStart: string, weekEnd: string): Promise<(Point & {id:string})[]> => {
  const db = getSupabase()
  // Throwing keeps an unavailable read out of the cache.
  if (!db) throw new Error("Activities unavailable")
  const rows: ActivityRow[] = []
  for(let offset=0;;offset+=500) {
    const {data,error} = await db.from("current_activities").select("id,location,postcode,venue_id,source_id,start_date,end_date,recurrence").order("id").range(offset,offset+499)
    if(error || !Array.isArray(data)) throw new Error("Activities unavailable")
    rows.push(...(data ?? []))
    if((data?.length ?? 0)<500) break
  }
  const points = await listingPoints(rows.filter(row => activeThisWeek(row,weekStart,weekEnd)), {requireVenues:true})
  return [...points].map(([id,point]) => ({id,...point}))
}, ["home-week-activity-points"], { revalidate: 900 })

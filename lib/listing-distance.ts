import 'server-only'
import { geocodeLocations, locationKey, distanceKm, kmToMiles } from './geo'
import type { Point } from './distance'
import { getSupabase } from './supabase'

type Listing={id:string;location:string|null;source_id?:string|null;postcode?:string|null;venue_id?:string|null}
/**
 * Resolves each public listing to its linked venue or geocoded location; unresolved listings are absent.
 * `requireVenues` throws when venue coordinates cannot be read, for callers that cache the result
 * and must not store a transient failure as reduced supply.
 */
export async function listingPoints<T extends Listing>(rows:T[],{requireVenues=false}:{requireVenues?:boolean}={}):Promise<Map<string,Point>> {
  const db=getSupabase()
  const ids=[...new Set(rows.map(r=>r.venue_id).filter((id):id is string=>Boolean(id)))]
  const linked=new Map<string,Point>()
  if(requireVenues&&ids.length&&!db) throw new Error('Venue coordinates unavailable')
  if(db&&ids.length){
    for(let i=0;i<ids.length;i+=100){
      const {data,error}=await db.from('venues').select('id,latitude,longitude').eq('public_visible',true).in('id',ids.slice(i,i+100))
      if(error&&requireVenues) throw new Error('Venue coordinates unavailable')
      for(const v of data??[]) if(typeof v.latitude==='number'&&typeof v.longitude==='number') linked.set(v.id,{lat:v.latitude,lng:v.longitude})
    }
  }
  const locatable=rows.map(r=>({...r,location:r.postcode ? `${r.location??''}, ${r.postcode}`:r.location}))
  const places=await geocodeLocations(locatable.filter(r=>!r.venue_id||!linked.has(r.venue_id)),true)
  const points=new Map<string,Point>()
  rows.forEach((r,i)=>{
    const location=(r.venue_id&&linked.get(r.venue_id))||places.get(locationKey(locatable[i]))
    if(location) points.set(r.id,location)
  })
  return points
}
/** Geocodes public listing locations, never the visitor's coordinates. */
export async function withDistances<T extends Listing>(rows:T[],point:Point):Promise<(T & {distance_miles:number|null})[]> {
  const points=await listingPoints(rows)
  return rows.map(r=>{
    const location=points.get(r.id)
    return {...r,distance_miles:location?kmToMiles(distanceKm(point,location)):null}
  })
}

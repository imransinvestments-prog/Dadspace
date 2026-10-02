import 'server-only'
import { geocodeLocations, locationKey, distanceKm, kmToMiles } from './geo'
import type { Point } from './distance'
import { getSupabase } from './supabase'

type Listing={id:string;location:string|null;source_id?:string|null;postcode?:string|null;venue_id?:string|null}
/** Geocodes public listing locations, never the visitor's coordinates. */
export async function withDistances<T extends Listing>(rows:T[],point:Point):Promise<(T & {distance_miles:number|null})[]> {
  const db=getSupabase()
  const ids=[...new Set(rows.map(r=>r.venue_id).filter((id):id is string=>Boolean(id)))]
  const linked=new Map<string,Point>()
  if(db&&ids.length){
    for(let i=0;i<ids.length;i+=100){
      const {data}=await db.from('venues').select('id,latitude,longitude').eq('public_visible',true).in('id',ids.slice(i,i+100))
      for(const v of data??[]) if(typeof v.latitude==='number'&&typeof v.longitude==='number') linked.set(v.id,{lat:v.latitude,lng:v.longitude})
    }
  }
  const locatable=rows.map(r=>({...r,location:r.postcode ? `${r.location??''}, ${r.postcode}`:r.location}))
  const places=await geocodeLocations(locatable.filter(r=>!r.venue_id||!linked.has(r.venue_id)),true)
  return rows.map((r,i)=>{
    const location=(r.venue_id&&linked.get(r.venue_id))||places.get(locationKey(locatable[i]))
    return {...r,distance_miles:location?kmToMiles(distanceKm(point,location)):null}
  })
}

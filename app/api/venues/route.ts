import { getSupabase } from '@/lib/supabase'
import { toVenue } from '@/lib/venues'
import { parsePoint } from '@/lib/distance'
import { publicVenuePage } from '@/lib/venue-discovery'
import { parseDiscoveryRadius } from '@/lib/discovery-radius'
export const dynamic='force-dynamic'
export async function GET(request:Request){
  const p=new URL(request.url).searchParams, point=parsePoint(p)
  if((p.has('lat')||p.has('lng'))&&!point)return Response.json({error:'Invalid location'},{status:400})
  const discovery=parseDiscoveryRadius(p)
  if(!discovery || discovery.scope==='online')return Response.json({error:'Invalid radius or scope'},{status:400})
  try {
  const db=getSupabase()
  if(!db)return Response.json({error:'Venues unavailable'},{status:503})
  const n=Number(p.get('offset')||0),offset=Number.isFinite(n)?Math.max(0,Math.floor(n)):0
  // Hydrated national browse pages must continue the exact same ordered read.
  const unfiltered=!point&&!(p.get('q')||'').trim()&&(!p.get('category')||p.get('category')==='all')&&p.get('free')!=='true'
  if(unfiltered&&offset%24===0){
    const result=await publicVenuePage({page:offset/24+1})
    if(result.loadFailed)return Response.json({error:'Venues unavailable'},{status:503})
    return Response.json({venues:result.venues,total:result.total,hasMore:result.hasMore},{headers:{'Cache-Control':'private, no-store'}})
  }
  // Indoor/outdoor capability data is not evidenced yet (#86); stale URLs
  // cannot activate unsupported filters. Radius eligibility precedes paging.
  const {data,error}=await db.rpc('discovery_venue_page',{p_lat:point?.lat??null,p_lng:point?.lng??null,p_query:(p.get('q')||'').trim().slice(0,100),p_category:p.get('category')||'all',p_free:p.get('free')==='true',p_offset:offset,p_limit:24,p_radius_km:discovery.radiusKm,p_scope:discovery.scope})
  if(error||!data)return Response.json({error:'Venues unavailable'},{status:503})
  return Response.json({venues:data.rows.map(toVenue).filter(Boolean),total:data.total,hasMore:offset+data.rows.length<data.total},{headers:{'Cache-Control':'private, no-store'}})
  } catch {return Response.json({error:'Venues unavailable'},{status:503,headers:{'Cache-Control':'private, no-store'}})}
}

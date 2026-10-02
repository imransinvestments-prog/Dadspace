import { getSupabase } from '@/lib/supabase'
import { toVenue } from '@/lib/venues'
import { parsePoint } from '@/lib/distance'
export const dynamic='force-dynamic'
export async function GET(request:Request){
  const p=new URL(request.url).searchParams, point=parsePoint(p)
  if((p.has('lat')||p.has('lng'))&&!point)return Response.json({error:'Invalid location'},{status:400})
  const db=getSupabase()
  if(!db)return Response.json({error:'Venues unavailable'},{status:503})
  const n=Number(p.get('offset')||0),offset=Number.isFinite(n)?Math.max(0,Math.floor(n)):0
  const {data,error}=await db.rpc('nearby_venue_page',{p_lat:point?.lat??null,p_lng:point?.lng??null,p_query:(p.get('q')||'').trim().slice(0,100),p_category:p.get('category')||'all',p_free:p.get('free')==='true',p_indoor:p.get('indoor')==='true',p_outdoor:p.get('outdoor')==='true',p_offset:offset,p_limit:24})
  if(error||!data)return Response.json({error:'Venues unavailable'},{status:503})
  return Response.json({venues:data.rows.map(toVenue).filter(Boolean),total:data.total,hasMore:offset+data.rows.length<data.total},{headers:{'Cache-Control':'private, no-store'}})
}

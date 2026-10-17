import { parseDiscoveryRadius } from '@/lib/discovery-radius'
import { fetchUpcomingEvents } from '@/lib/events'
import { parsePoint } from '@/lib/distance'
export const dynamic='force-dynamic'
export const maxDuration=60
export async function GET(request:Request){
  const params=new URL(request.url).searchParams
  const discovery=parseDiscoveryRadius(params)
  if(!discovery)return Response.json({error:'Invalid radius or scope'},{status:400})
  const point=parsePoint(params)
  if((params.has('lat')||params.has('lng'))&&!point)return Response.json({error:'Invalid location'},{status:400})
  try{
    const result=await fetchUpcomingEvents(point,discovery.radiusKm,discovery.scope)
    if(result.loadFailed)return Response.json({error:'Events unavailable'},{status:503,headers:{'Cache-Control':'private, no-store'}})
    return Response.json(result,{headers:{'Cache-Control':'private, no-store'}})
  }
  catch{return Response.json({error:'Events unavailable'},{status:503})}
}

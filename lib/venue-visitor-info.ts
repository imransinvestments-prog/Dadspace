import 'server-only'
import { getSupabase } from './supabase'
import { publicEvidenceUrl } from './operations/review-edit'
export async function venueVisitorInfo(id:string):Promise<{source_url:string;checked_at:string;reviewed_fields:string[]}|null>{
 try {
  const db=getSupabase()
  if(!db)return null
  const {data,error}=await db.rpc('dadspace_public_venue_visitor_info',{p_id:id}).abortSignal(AbortSignal.timeout(3000))
  if(error || !data || !publicEvidenceUrl(data.source_url) || typeof data.checked_at!=='string' || !Number.isFinite(Date.parse(data.checked_at)))return null
  const fields=Array.isArray(data.reviewed_fields)?data.reviewed_fields.filter((f:unknown):f is string=>typeof f==='string' && ['opening_hours','fee','access','website'].includes(f)):[]
  if(!fields.length)return null
  return {source_url:data.source_url,checked_at:data.checked_at,reviewed_fields:fields}
 }catch{return null}
}

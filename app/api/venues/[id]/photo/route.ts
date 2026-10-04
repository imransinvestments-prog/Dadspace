import { getSupabase } from '@/lib/supabase'
import { googleApiKey, googlePlaceId, fetchVenuePhoto } from '@/lib/google-venue-photos.mjs'

export const dynamic = 'force-dynamic'
const headers = { 'Cache-Control': 'private, no-store' }
export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  if (!/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(id)) return Response.json({photo:null},{status:400,headers})
  const db = getSupabase(), apiKey = googleApiKey()
  if (!db || !apiKey) return Response.json({photo:null},{status:503,headers})
  // Only resolve a place associated with an existing public venue. The caller
  // cannot use this endpoint as an arbitrary Google Places proxy.
  const {data,error} = await db.from('venues').select('image_url').eq('id',id).eq('public_visible',true).maybeSingle()
  const placeId = googlePlaceId(data?.image_url)
  if (error || !placeId) return Response.json({photo:null},{status:404,headers})
  try { return Response.json({photo:await fetchVenuePhoto(placeId,apiKey)},{headers}) }
  catch { return Response.json({photo:null},{status:502,headers}) }
}

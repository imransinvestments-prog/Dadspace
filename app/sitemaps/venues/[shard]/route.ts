import { getSupabase } from "@/lib/supabase"
import { isProduction, siteUrl } from "@/lib/seo"
import { venueSlug } from "@/lib/venue-slug"
import { urlset, xmlHeaders } from "@/lib/sitemap-xml"
import { COMING_SOON } from "@/lib/launch"
export const dynamic = "force-dynamic"
export async function GET(_request:Request, {params}:{params:Promise<{shard:string}>}) {
  const {shard} = await params
  if(!/^[0-9a-f]\.xml$/.test(shard)) return new Response("Not found",{status:404})
  if(!isProduction||COMING_SOON) return new Response(urlset([]),{headers:xmlHeaders})
  const db = getSupabase()
  if(!db) return new Response("Sitemap temporarily unavailable",{status:503})
  const prefix=shard[0], lower=`${prefix}0000000-0000-0000-0000-000000000000`, upper=`${prefix}fffffff-ffff-ffff-ffff-ffffffffffff`
  const entries:{url:string}[]=[]
  let after:string|null=null
  // Keyset batches avoid Supabase's per-response cap. Disjoint UUID shards cover the whole catalogue.
  while(true) {
    let query=db.from("venues").select("id,venue_name,venue_label").eq("public_visible",true).gte("id",lower).lte("id",upper).order("id").limit(1000)
    if(after) query=query.gt("id",after)
    const {data,error}=await query
    if(error) return new Response("Sitemap temporarily unavailable",{status:503})
    if(!data?.length) break
    for(const row of data) if(row.venue_name||row.venue_label) entries.push({url:`${siteUrl}/venues/${venueSlug({id:String(row.id),name:String(row.venue_name||row.venue_label)})}`})
    if(entries.length>50000) return new Response("Sitemap shard requires splitting",{status:503})
    after=String(data.at(-1)!.id)
  }
  return new Response(urlset(entries),{headers:xmlHeaders})
}

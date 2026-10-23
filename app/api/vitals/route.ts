import { getSupabase } from "@/lib/supabase"
import { isProduction } from "@/lib/seo"
import { parseVital } from "@/lib/web-vitals"
export const dynamic="force-dynamic"
const MAX_BODY=2048
// A beacon never reads the reply, so every outcome is the same empty 204.
const done=()=>new Response(null,{status:204,headers:{"Cache-Control":"no-store"}})
export async function POST(request:Request) {
  // Preview and local traffic would mix test devices into production field data.
  if(!isProduction) return done()
  const body=await request.text().catch(()=>"")
  if(!body||body.length>MAX_BODY) return done()
  let input:unknown
  try {input=JSON.parse(body)} catch {return done()}
  const row=parseVital(input,request.headers.get("user-agent"))
  const db=getSupabase()
  if(!row||!db) return done()
  // A metric id is one page load's report; a resent beacon must not count twice.
  const {error}=await db.from("web_vitals").upsert(row,{onConflict:"metric_id",ignoreDuplicates:true})
  if(error) console.error("web vitals insert failed",error.code)
  return done()
}

import { NextResponse } from "next/server"
import { getSupabase } from "@/lib/supabase"
export const dynamic = "force-dynamic"
export async function GET() {
  const db = getSupabase()
  if(!db) return NextResponse.json({error:"Deals unavailable"},{status:503})
  const {data,error} = await db.from("deals").select("id,title,description,retailer,price,was_price,discount_pct,image_url,link").eq("status","live").order("posted_at",{ascending:false,nullsFirst:false}).limit(3)
  if(error) return NextResponse.json({error:"Deals unavailable"},{status:503})
  return NextResponse.json(data ?? [])
}

import { NextResponse } from "next/server"
import { getDeals } from "@/lib/deals"
export const dynamic = "force-dynamic"
export async function GET() {
  const { items, loadFailed } = await getDeals()
  if(loadFailed) return NextResponse.json({error:"Deals unavailable"},{status:503})
  return NextResponse.json(items.slice(0, 3), { headers: { "Cache-Control": "no-store" } })
}

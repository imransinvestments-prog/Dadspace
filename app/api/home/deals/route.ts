import { NextResponse } from "next/server"
import { getDeals } from "@/lib/deals"
export const dynamic = "force-dynamic"
export async function GET() {
  const { items, loadFailed } = await getDeals()
  if(loadFailed) return NextResponse.json({error:"Deals unavailable"},{status:503})
  // Identical for every visitor, so the CDN can answer polls; the short TTL bounds how long an expiring offer lingers.
  return NextResponse.json(items.slice(0, 3), { headers: { "Cache-Control": "public, s-maxage=60, stale-while-revalidate=60" } })
}

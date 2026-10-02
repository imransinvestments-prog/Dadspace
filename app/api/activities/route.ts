import { NextRequest, NextResponse } from "next/server"
import { ACTIVITY_PAGE_SIZE, fetchActivityPage } from "@/lib/activities"
import { parsePoint } from '@/lib/distance'

export const dynamic = 'force-dynamic'
export const maxDuration = 60

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const offset = Number(searchParams.get("offset") || "0")
  const limit = Number(searchParams.get("limit") || String(ACTIVITY_PAGE_SIZE))
  const query = searchParams.get("q")
  const category = searchParams.get("category")
  const point = parsePoint(searchParams)
  if((searchParams.has('lat')||searchParams.has('lng'))&&!point)return NextResponse.json({error:'Invalid location'},{status:400})

  try {
  const page = await fetchActivityPage({
    offset: Number.isFinite(offset) ? Math.max(0,Math.floor(offset)) : 0,
    limit: Number.isFinite(limit) ? Math.floor(limit) : ACTIVITY_PAGE_SIZE,
    query,
    category,
    point,
  })

  return NextResponse.json(page, {
    headers: { "Cache-Control": "private, no-store" },
  })
  } catch {return NextResponse.json({error:'Activities unavailable'},{status:503})}
}

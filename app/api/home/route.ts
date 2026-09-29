import { getHomeData } from "@/lib/data"

export const dynamic = "force-dynamic"

export async function GET() {
  const data = await getHomeData()
  return Response.json(data, { headers: { "Cache-Control": "no-store" } })
}

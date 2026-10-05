import { HomeDashboard } from "@/components/home/home-dashboard"
import { getHomeData } from "@/lib/data"
import { COMING_SOON } from "@/lib/launch"

export const dynamic = "force-dynamic"

export default async function HomePage() {
  if (COMING_SOON) return null
  const data = await getHomeData()
  return <HomeDashboard initial={data} />
}

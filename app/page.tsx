import { HomeDashboard } from "@/components/home/home-dashboard"
import { getHomeData } from "@/lib/data"

export const dynamic = "force-dynamic"

export default async function HomePage() {
  const data = await getHomeData()
  return <HomeDashboard initial={data} />
}

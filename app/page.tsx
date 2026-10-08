import { HomeDashboard } from "@/components/home/home-dashboard"
import { getHomeData } from "@/lib/data"
import { COMING_SOON } from "@/lib/launch"
import { publicVenuePage } from "@/lib/venue-discovery"
import { getDeals } from "@/lib/deals"
import { DiscoveryLinks } from "@/components/venues/discovery-links"

export const dynamic = "force-dynamic"

export default async function HomePage() {
  if (COMING_SOON) return null
  const [data, places, deals] = await Promise.all([getHomeData(), publicVenuePage(), getDeals()])
  return <HomeDashboard initial={data} publicPlaces={places.venues.slice(0,6)} initialDeals={deals.items.slice(0,3)}><DiscoveryLinks/></HomeDashboard>
}

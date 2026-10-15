import { HomeDashboard } from "@/components/home/home-dashboard"
import { getHomeData } from "@/lib/data"
import { COMING_SOON } from "@/lib/launch"
import { publicVenuePage } from "@/lib/venue-discovery"
import { getDeals } from "@/lib/deals"
import { DiscoveryLinks } from "@/components/venues/discovery-links"
import Link from "next/link"

export const dynamic = "force-dynamic"

export default async function HomePage() {
  if (COMING_SOON) return null
  const [data, places, deals] = await Promise.all([getHomeData(), publicVenuePage(), getDeals()])
  return <HomeDashboard initial={data} publicPlaces={places.venues.slice(0,6)} initialDeals={deals.items.slice(0,3)}><Link href="/auth/login?next=%2Fops" className="inline-flex w-fit rounded-lg border px-5 py-3 font-semibold hover:bg-muted">Operations login</Link><DiscoveryLinks/></HomeDashboard>
}

import { HomeDashboard } from "@/components/home/home-dashboard"
import { getHomeData } from "@/lib/data"
import { COMING_SOON } from "@/lib/launch"
import { publicVenuePage } from "@/lib/venue-discovery"
import { getDeals } from "@/lib/deals"
import { DiscoveryLinks } from "@/components/venues/discovery-links"
import Link from "next/link"
import { AwinPublisherTag } from "@/components/awin-publisher-tag"

// Nothing here depends on the visitor (location-aware sections load client-side),
// so one render serves everyone for up to five minutes.
export const revalidate = 300

export default async function HomePage() {
  if (COMING_SOON) return null
  const [data, places, deals] = await Promise.all([getHomeData(), publicVenuePage(), getDeals()])
  // A failed regeneration keeps serving the last good page rather than caching an outage for every
  // visitor. Builds and unconfigured environments still render, so a deploy never depends on the database.
  if ((places.loadFailed || deals.loadFailed) && process.env.NEXT_PHASE !== "phase-production-build" && process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY) {
    throw new Error("Homepage data unavailable")
  }
  return <><HomeDashboard data={data} publicPlaces={places.venues.slice(0,6)} initialDeals={deals.items.slice(0,3)}><Link href="/auth/login?next=%2Fops" className="inline-flex w-fit rounded-lg border px-5 py-3 font-semibold hover:bg-muted">Operations login</Link><DiscoveryLinks/></HomeDashboard><AwinPublisherTag /></>
}

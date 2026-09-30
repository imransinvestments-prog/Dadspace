import { ComingSoon } from "@/components/coming-soon"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Family Events",
  "/events",
  "Discover family-friendly events, days out and activities for dads and children across the UK.",
)

export default function EventsPage() {
  return <ComingSoon title="Events" joke="Filters, maps and saved days out are on the way. Like flat-pack furniture, it'll take longer than the box says." />
}

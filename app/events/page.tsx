import type { Metadata } from "next"
import { ComingSoon } from "@/components/coming-soon"

export const metadata: Metadata = { title: "Events" }

export default function EventsPage() {
  return <ComingSoon title="Events" joke="Filters, maps and saved days out are on the way. Like flat-pack furniture, it'll take longer than the box says." />
}

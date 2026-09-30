import { ComingSoon } from "@/components/coming-soon"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Family Deals",
  "/deals",
  "Find family-focused discounts, offers and bargains on baby gear, kids' essentials, days out and more.",
)

export default function DealsPage() {
  return <ComingSoon title="Deals" joke="We're hunting down bargains on buggies and nappies. Unlike your car keys, these we'll actually find." />
}

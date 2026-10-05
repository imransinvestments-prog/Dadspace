import { SectionHeader } from "./section-header"
import { DealCard } from "@/components/deal-card"
import type { HomeData } from "@/lib/types"

export function TopDeal({ deal }: { deal: HomeData["deal"] }) {
  return (
    <section aria-labelledby="deal-title" className="flex flex-col gap-4">
      <SectionHeader id="deal-title" title="Deals worth a look" href="/deals" linkLabel="View all deals" />
      {deal.items ? <DealCard deal={deal.items} /> : (
        <p className="rounded-2xl border bg-card p-5 text-muted-foreground">
          {deal.loadFailed ? "We couldn’t load offers just now. Please try again shortly." : "No offers meet our quality checks right now. Check back soon."}
        </p>
      )}
    </section>
  )
}


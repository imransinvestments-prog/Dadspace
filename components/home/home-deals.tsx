"use client"
import useSWR from "swr"
import { SectionHeader } from "./section-header"
import { DealCard } from "@/components/deal-card"
import type { LiveDeal } from "@/lib/deals-selection"
const fetcher = async (url: string): Promise<LiveDeal[]> => {
  const response = await fetch(url)
  if (!response.ok) throw new Error("Unavailable")
  return response.json()
}
export function HomeDeals() {
  const { data, error, isLoading } = useSWR("/api/home/deals", fetcher, { refreshInterval: 300000 })
  return <section aria-labelledby="home-deals-title" className="flex flex-col gap-4">
    <SectionHeader id="home-deals-title" title="Deals for dads" href="/deals" linkLabel="All deals" />
    <div className="grid gap-4 md:grid-cols-3">{data?.map(deal => <DealCard key={deal.id} deal={deal} />)}</div>
    {!data?.length && <p className="text-muted-foreground">{isLoading ? "Loading deals…" : error ? "Deals are temporarily unavailable." : "No offers meet our quality checks right now. Check back soon."}</p>}
  </section>
}

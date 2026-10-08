import { Tag } from "lucide-react"
import { getDeals, getDealGroups } from "@/lib/deals"
import Link from "next/link"
import { DealCard } from "@/components/deal-card"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Family Deals",
  "/deals",
  "Find family-focused discounts, offers and bargains on baby gear, kids' essentials, toys and more.",
  {image:"/images/news/money.png"},
)

export const revalidate = 900

export default async function DealsPage({ searchParams }: { searchParams: Promise<{ group?: string }> }) {
  const [{ items, loadFailed }, groups, params] = await Promise.all([getDeals(), getDealGroups(), searchParams])
  const group = groups.includes(params.group ?? "") ? params.group : undefined
  const deals = group ? items.filter(deal => deal.display_group === group) : items

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-8 rounded-3xl border border-white/10 bg-card/70 p-6 sm:p-8">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-cyan-400">
          <Tag className="h-4 w-4" />
          Family bargains
        </div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Deals worth a dad look</h1>
        <p className="mt-3 max-w-3xl text-base text-muted-foreground sm:text-lg">
          Offers on baby gear, kids&apos; essentials, toys, family kit and days out. We filter the noise so you don&apos;t have to.
        </p>
      </section>

      <nav aria-label="Deal categories" className="mb-6 flex flex-wrap gap-2">
        {["All offers", ...groups].map(label => {
          const active = label === (group ?? "All offers")
          return <Link key={label} href={label === "All offers" ? "/deals" : `/deals?group=${encodeURIComponent(label)}`}
            aria-current={active ? "page" : undefined}
            className={`rounded-full border px-4 py-2 text-sm ${active ? "bg-orange-500 text-slate-950" : "bg-card"}`}>
            {label}
          </Link>
        })}
      </nav>

      {loadFailed ? (
        <div className="rounded-2xl border border-white/10 bg-card p-6 text-muted-foreground">
          We couldn&apos;t load deals just now. Please try again shortly.
        </div>
      ) : deals.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-card p-6 text-muted-foreground">
          {group ? `No ${group.toLowerCase()} offers meet our quality checks right now.` : "No offers meet our quality checks right now."} Check back soon.
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-muted-foreground">{deals.length} source-listed offers</div>
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {deals.map((deal) => <DealCard key={deal.id} deal={deal} />)}
          </div>
        </>
      )}
    </main>
  )
}

import Image from "next/image"
import Link from "next/link"
import { SectionHeader } from "./section-header"
import type { HomeData } from "@/lib/types"

const gbp = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP", maximumFractionDigits: 0 })

export function TopDeal({ deal }: { deal: HomeData["deal"] }) {
  const d = deal.items
  const discount = Math.round((1 - d.price / d.oldPrice) * 100)

  return (
    <section aria-labelledby="deal-title" className="flex flex-col gap-4">
      <SectionHeader id="deal-title" title="Deals worth a look" href="/deals" linkLabel="View all deals" isSample={deal.isSample} />
      <Link
        href="/deals"
        className="group flex flex-col overflow-hidden rounded-lg border bg-card transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-navy/10"
      >
        <div className="relative aspect-[16/9] bg-muted">
          <Image src={d.image || "/placeholder.svg"} alt={d.title} fill sizes="(min-width: 1024px) 30vw, 100vw" className="object-cover transition duration-500 group-hover:scale-105" />
          <span className="absolute top-3 left-3 flex size-16 -rotate-12 flex-col items-center justify-center rounded-full bg-highlight font-heading leading-none font-extrabold text-highlight-foreground">
            <span className="text-lg">{discount}%</span>
            <span className="text-xs">off</span>
          </span>
        </div>
        <div className="flex flex-col gap-2 p-4">
          <p className="text-xs font-bold tracking-wide text-accent uppercase">
            {d.category} · {d.retailer}
          </p>
          <h3 className="font-heading text-lg leading-snug font-bold">{d.title}</h3>
          <p className="flex items-baseline gap-2">
            <span className="font-heading text-2xl font-extrabold text-primary">{gbp.format(d.price)}</span>
            <span className="text-sm text-muted-foreground line-through">
              <span className="sr-only">Was </span>
              {gbp.format(d.oldPrice)}
            </span>
          </p>
          <p className="text-xs text-muted-foreground">We may earn a commission if you buy through our links.</p>
        </div>
      </Link>
    </section>
  )
}

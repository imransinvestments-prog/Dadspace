import { ExternalLink } from "lucide-react"
import { dealBenefit, merchantAdvertised, type LiveDeal } from "@/lib/deals-selection"

const gbp = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" })

export function DealCard({ deal }: { deal: LiveDeal }) {
  const benefit = dealBenefit(deal)
  const advertised = merchantAdvertised(deal)
  return (
    <article className="overflow-hidden rounded-2xl border bg-card shadow-sm">
      {deal.image_url ? (
        <div className="aspect-[16/9] overflow-hidden bg-muted">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={deal.image_url} alt="" className="h-full w-full object-cover" loading="lazy" referrerPolicy="no-referrer" />
        </div>
      ) : null}
      <div className="flex flex-col gap-3 p-5">
        <p className="text-xs font-semibold text-cyan-400">{deal.display_group} · {deal.retailer ?? "See source for retailer"}</p>
        <h3 className="text-lg font-bold leading-snug">{deal.title}</h3>
        {advertised && <p className="text-xs font-semibold text-orange-400">Merchant-advertised sale</p>}
        {benefit ? <p className="font-bold text-orange-400">{benefit}</p> : (
          <p className="text-sm">
            <strong className="text-2xl text-orange-400">{gbp.format(Number(deal.price))}</strong>
            {advertised
              ? <> · Merchant comparison price {gbp.format(Number(deal.was_price))}</>
              : <> · {Math.round(Number(deal.discount_pct))}% below source comparison ({gbp.format(Number(deal.was_price))})</>}
          </p>
        )}
        {advertised && <p className="text-xs text-muted-foreground">Comparison price supplied by the merchant; previous selling price and savings have not been independently verified.</p>}
        {deal.description && deal.description.length > 400 ? (
          <details className="text-sm leading-6 text-muted-foreground">
            <summary className="cursor-pointer">Offer details and conditions</summary>
            <p className="mt-2">{deal.description}</p>
          </details>
        ) : <p className="text-sm leading-6 text-muted-foreground">{deal.description || "Check the source for full terms and availability."}</p>}
        <p className="text-xs text-muted-foreground">
          Listed by source · Last seen {new Date(deal.last_seen!).toLocaleString("en-GB", { timeZone: "Europe/London" })}.
          {deal.expires_at ? ` Ends ${new Date(deal.expires_at).toLocaleDateString("en-GB", { timeZone: "Europe/London" })}.` : " End date not supplied."}
          {" "}Check the final price, delivery, eligibility and availability before buying.
        </p>
        <a href={deal.link} target="_blank" rel="nofollow sponsored noopener noreferrer"
          className="inline-flex w-fit items-center gap-2 rounded-full bg-orange-500 px-4 py-2.5 text-sm font-bold text-slate-950 hover:bg-orange-400">
          View offer and terms <ExternalLink className="h-4 w-4" />
        </a>
        <p className="text-xs text-muted-foreground">We may earn a commission through some links. This does not affect ranking.</p>
      </div>
    </article>
  )
}


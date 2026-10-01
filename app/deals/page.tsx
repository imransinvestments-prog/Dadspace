import { ExternalLink, Tag } from "lucide-react"
import { getSupabase } from "@/lib/supabase"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Family Deals",
  "/deals",
  "Find family-focused discounts, offers and bargains on baby gear, kids' essentials, toys and more.",
)

export const revalidate = 900

type Deal = {
  id: number | string
  title: string
  description: string | null
  retailer: string | null
  price: number | null
  was_price: number | null
  discount_pct: number | null
  image_url: string | null
  display_group: string | null
  link: string
  posted_at: string | null
}

function money(value: number | null) {
  if (value == null || Number.isNaN(Number(value))) return null
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(Number(value))
}

export default async function DealsPage() {
  const supabase = getSupabase()
  let deals: Deal[] = []
  let loadFailed = false

  if (supabase) {
    const { data, error } = await supabase
      .from("deals")
      .select("id,title,description,retailer,price,was_price,discount_pct,image_url,display_group,link,posted_at")
      .eq("status", "live")
      .order("posted_at", { ascending: false, nullsFirst: false })
      .limit(60)

    if (error) loadFailed = true
    else deals = (data ?? []) as Deal[]
  } else {
    loadFailed = true
  }

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-8 rounded-3xl border border-white/10 bg-card/70 p-6 sm:p-8">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-cyan-400">
          <Tag className="h-4 w-4" />
          Family bargains
        </div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">Deals worth a dad look</h1>
        <p className="mt-3 max-w-3xl text-base text-muted-foreground sm:text-lg">
          Fresh offers on baby gear, kids&apos; essentials, toys and family kit. We filter the noise so you don&apos;t have to.
        </p>
      </section>

      {loadFailed ? (
        <div className="rounded-2xl border border-white/10 bg-card p-6 text-muted-foreground">
          We couldn&apos;t load deals just now. Please try again shortly.
        </div>
      ) : deals.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-card p-6 text-muted-foreground">
          No live deals are available right now. Check back soon.
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-muted-foreground">{deals.length} live deals</div>
          <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {deals.map((deal) => {
              const price = money(deal.price)
              const wasPrice = money(deal.was_price)
              const discount = deal.discount_pct != null && Number(deal.discount_pct) > 0
                ? Math.round(Number(deal.discount_pct))
                : null

              return (
                <article key={deal.id} className="overflow-hidden rounded-2xl border border-white/10 bg-card shadow-sm">
                  {deal.image_url ? (
                    <div className="aspect-[16/9] overflow-hidden bg-muted">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={deal.image_url}
                        alt=""
                        className="h-full w-full object-cover"
                        loading="lazy"
                        referrerPolicy="no-referrer"
                      />
                    </div>
                  ) : null}

                  <div className="flex h-full flex-col p-5">
                    <div className="mb-3 flex flex-wrap items-center gap-2 text-xs font-semibold">
                      {deal.display_group ? (
                        <span className="rounded-full bg-cyan-500/10 px-2.5 py-1 text-cyan-300">{deal.display_group}</span>
                      ) : null}
                      {discount ? (
                        <span className="rounded-full bg-orange-500/15 px-2.5 py-1 text-orange-300">{discount}% off</span>
                      ) : null}
                    </div>

                    <h2 className="text-lg font-bold leading-snug">{deal.title}</h2>
                    {deal.retailer ? <p className="mt-2 text-sm text-muted-foreground">{deal.retailer}</p> : null}

                    {(price || wasPrice) ? (
                      <div className="mt-4 flex items-baseline gap-2">
                        {price ? <span className="text-2xl font-extrabold text-orange-400">{price}</span> : null}
                        {wasPrice && wasPrice !== price ? (
                          <span className="text-sm text-muted-foreground line-through">{wasPrice}</span>
                        ) : null}
                      </div>
                    ) : null}

                    {deal.description ? (
                      <p className="mt-3 line-clamp-3 text-sm leading-6 text-muted-foreground">{deal.description}</p>
                    ) : null}

                    <a
                      href={deal.link}
                      target="_blank"
                      rel="nofollow sponsored noopener noreferrer"
                      className="mt-5 inline-flex w-fit items-center gap-2 rounded-full bg-orange-500 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-orange-400"
                    >
                      View deal <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </article>
              )
            })}
          </div>
        </>
      )}
    </main>
  )
}

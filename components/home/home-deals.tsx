"use client"
import useSWR from "swr"
import { SectionHeader } from "./section-header"
type Deal={id:string;title:string;description:string|null;retailer:string|null;price:number|null;was_price:number|null;discount_pct:number|null;image_url:string|null;link:string}
const fetcher=async(url:string):Promise<Deal[]>=>{const r=await fetch(url);if(!r.ok)throw new Error("Unavailable");return r.json()}
const price=(value:number)=>new Intl.NumberFormat("en-GB",{style:"currency",currency:"GBP"}).format(value)
export function HomeDeals(){
  const {data,error,isLoading}=useSWR("/api/home/deals",fetcher,{refreshInterval:300000})
  return <section aria-labelledby="home-deals-title" className="flex flex-col gap-4">
    <SectionHeader id="home-deals-title" title="Deals for dads" href="/deals" linkLabel="All deals"/>
    <div className="grid gap-4 md:grid-cols-3">{data?.map(deal=><a key={deal.id} href={deal.link} target="_blank" rel="nofollow sponsored noopener noreferrer" className="flex min-w-0 flex-col overflow-hidden rounded-xl border bg-card transition hover:shadow-lg">
      {deal.image_url && <img src={deal.image_url} alt="" loading="lazy" referrerPolicy="no-referrer" className="h-44 w-full bg-white object-contain p-4"/>}
      <div className="flex flex-1 flex-col gap-3 p-5"><p className="text-xs font-bold uppercase text-accent">{deal.retailer}</p><h3 className="font-heading text-lg font-bold">{deal.title}</h3>{deal.description && <p className="line-clamp-3 text-sm text-muted-foreground">{deal.description}</p>}<p className="mt-auto font-bold">{deal.price != null ? price(deal.price) : "Check retailer price"}{deal.was_price != null && deal.price != null && deal.was_price > deal.price && <del className="ml-2 text-sm font-normal text-muted-foreground">{price(deal.was_price)}</del>}</p><span className="text-sm font-semibold text-accent">View deal →<span className="sr-only"> (opens in a new tab)</span></span></div>
    </a>)}</div>
    {!data?.length && <p className="text-muted-foreground">{isLoading ? "Loading deals…" : error ? "Deals are temporarily unavailable." : "New deals are on their way."}</p>}
  </section>
}

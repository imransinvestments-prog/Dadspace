import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { VenuesDirectory } from "@/components/venues/venues-directory"
import { VenuesJsonLd } from "@/components/venues/venues-json-ld"
import { DiscoveryLinks } from "@/components/venues/discovery-links"
import { publicVenuePage } from "@/lib/venue-discovery"
import { browsePage } from "@/lib/venue-slug"
import { pageMetadata } from "@/lib/seo"
import { getSupabase } from "@/lib/supabase"
export const dynamic = "force-dynamic"
type Props = {searchParams: Promise<Record<string, string | string[] | undefined>>}
export async function generateMetadata({searchParams}: Props): Promise<Metadata> {
  const search = await searchParams, page = browsePage(search.page)
  if (!page) notFound()
  return pageMetadata(`UK venues for family days out${page > 1 ? ` – page ${page}` : ""}`, `/venues${page > 1 ? `?page=${page}` : ""}`, "Browse published UK venues, museums, libraries, play spaces and more. Choose a location for nearby results.", {image:"/images/venues/playground.png",noIndex:Object.keys(search).some(k=>k!=="page")})
}
export default async function VenuesPage({searchParams}: Props) {
  const page = browsePage((await searchParams).page)
  if (!page) notFound()
  const initial = await publicVenuePage({page})
  if (initial.loadFailed) throw new Error("Venues are temporarily unavailable")
  if (page > 1 && !initial.venues.length) notFound()
  const db = getSupabase()
  const {data: categories} = db ? await db.rpc("venue_category_counts") : {data:null}
  return <>
    <VenuesJsonLd venues={initial.venues} path={`/venues${page > 1 ? `?page=${page}` : ""}`}/>
    <VenuesDirectory venues={initial.venues} initialTotal={initial.total} initialHasMore={initial.hasMore} initialPage={page} allCategories={categories??[]}/>
    <DiscoveryLinks/>
    <nav aria-label="Browse all UK venue pages" className="flex justify-between">{page > 1 && <Link href={page > 2 ? `/venues?page=${page-1}` : "/venues"}>← Previous UK page</Link>}{initial.hasMore && <Link href={`/venues?page=${page+1}`}>Next UK page →</Link>}</nav>
  </>
}

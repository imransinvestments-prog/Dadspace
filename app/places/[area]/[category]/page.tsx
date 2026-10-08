import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { discoveryArea, discoveryCategory, publicVenuePage } from "@/lib/venue-discovery"
import { browsePage } from "@/lib/venue-slug"
import { pageMetadata } from "@/lib/seo"
import { VenueCard } from "@/components/venues/venue-card"
import { VenuesJsonLd } from "@/components/venues/venues-json-ld"
export const dynamic = "force-dynamic"
type Props = { params: Promise<{area: string; category: string}>; searchParams: Promise<{page?: string; [key: string]: string | string[] | undefined}> }
async function context({ params, searchParams }: Props) {
  const p = await params, search = await searchParams
  const area = discoveryArea(p.area), category = discoveryCategory(p.category), page = browsePage(search.page)
  if (!area || !category || !page) notFound()
  const result = await publicVenuePage({ town: area.name, category: category.raw, page })
  if (result.loadFailed) throw new Error("Places are temporarily unavailable")
  if (page > 1 && !result.venues.length) notFound()
  const path = `/places/${area.slug}/${category.slug}${page > 1 ? `?page=${page}` : ""}`
  return { area, category, page, result, path, filtered: Object.keys(search).some(k => k !== "page") }
}
export async function generateMetadata(props: Props): Promise<Metadata> {
  const { area, category, page, result, path, filtered } = await context(props)
  return pageMetadata(`${category.name} in ${area.name}${page > 1 ? ` – page ${page}` : ""}`, path, `Browse ${category.name.toLowerCase()} in ${area.name}, with addresses and available visitor information for your next family visit.`, {image: category.image, noIndex: result.total < 3 || filtered})
}
export default async function AreaCategoryPage(props: Props) {
  const { area, category, page, result, path } = await context(props)
  return <div className="flex flex-col gap-6">
    <nav aria-label="Breadcrumb"><Link href="/">Home</Link> / <Link href="/venues">Venues</Link> / {area.name}</nav>
    <header><h1 className="font-heading text-4xl font-bold">{category.name} in {area.name}</h1><p className="mt-4 max-w-2xl text-muted-foreground">{area.intro}</p><p className="mt-2 text-sm">{result.total} published places · page {page}. Check suitability, prices and opening times with the venue before travelling.</p></header>
    <VenuesJsonLd venues={result.venues} path={path} title={`${category.name} in ${area.name}`} />
    {result.venues.length ? <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">{result.venues.map(venue => <li key={venue.id}><VenueCard venue={venue} distance={null}/></li>)}</ul> : <p>No published places are available in this category yet.</p>}
    <nav aria-label="Listing pages" className="flex justify-between">{page > 1 && <Link href={`${path.split("?")[0]}${page > 2 ? `?page=${page - 1}` : ""}`}>← Previous page</Link>}{result.hasMore && <Link href={`${path.split("?")[0]}?page=${page + 1}`}>Next page →</Link>}</nav>
  </div>
}

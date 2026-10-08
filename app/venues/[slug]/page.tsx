import type { Metadata } from "next"
import Link from "next/link"
import { notFound, permanentRedirect } from "next/navigation"
import { publicVenueById } from "@/lib/venue-discovery"
import { venueIdFromSlug, venueSlug } from "@/lib/venue-slug"
import { categoryImage, categoryLabel, FACILITY_LABELS, venuePhotoUrl } from "@/lib/venue-meta"
import { pageMetadata, siteUrl } from "@/lib/seo"
import { VenuePhoto } from "@/components/venues/venue-photo"
import { venueSchema } from "@/components/venues/venues-json-ld"
import { JsonLd } from "@/components/seo/json-ld"
import { directionsUrl } from "@/components/venues/venue-spotlight"
export const dynamic = "force-dynamic"
type Props = {params: Promise<{slug: string}>}
async function venueFor(props: Props) {
  const {slug} = await props.params, id = venueIdFromSlug(slug)
  if (!id) notFound()
  const venue = await publicVenueById(id)
  if (!venue) notFound()
  if (slug !== venueSlug(venue)) permanentRedirect(`/venues/${venueSlug(venue)}`)
  return venue
}
export async function generateMetadata(props: Props): Promise<Metadata> {
  const v = await venueFor(props)
  return pageMetadata(`${v.name}${v.town ? ` in ${v.town}` : ""}`, `/venues/${venueSlug(v)}`, `${categoryLabel(v.category)}${v.town ? ` in ${v.town}` : ""}. Find the address and available visitor information for ${v.name}.`, {image: venuePhotoUrl(v) ?? categoryImage(v.category)})
}
export default async function VenueDetail(props: Props) {
  const v = await venueFor(props), url = `${siteUrl}/venues/${venueSlug(v)}`
  return <div className="flex flex-col gap-6">
    <nav aria-label="Breadcrumb"><Link href="/">Home</Link> / <Link href="/venues">Venues</Link> / {v.name}</nav>
    <JsonLd data={{"@context":"https://schema.org","@graph":[{...venueSchema(v),"@id":`${url}#venue`,url},{"@type":"BreadcrumbList",itemListElement:[{"@type":"ListItem",position:1,name:"Home",item:siteUrl},{"@type":"ListItem",position:2,name:"Venues",item:`${siteUrl}/venues`},{"@type":"ListItem",position:3,name:v.name,item:url}]}]}}/>
    <header><p className="text-sm font-semibold text-accent">{categoryLabel(v.category)}</p><h1 className="mt-2 font-heading text-4xl font-bold">{v.name}</h1>{v.town && <p className="mt-2 text-muted-foreground">{v.town}</p>}</header>
    <div className="grid gap-6 md:grid-cols-2"><div className="relative aspect-[16/10] overflow-hidden rounded-xl"><VenuePhoto venue={v} sizes="(min-width: 768px) 480px, 100vw" /></div>
    <section aria-label="Visitor information" className="rounded-xl border bg-card p-6"><dl className="space-y-4">
      <div><dt className="font-semibold">Address</dt><dd>{[v.address,v.town,v.postcode].filter(Boolean).join(", ") || "Not supplied"}</dd></div>
      <div><dt className="font-semibold">Opening times</dt><dd>{v.opening_hours || "Check with the venue"}</dd></div>
      <div><dt className="font-semibold">Entry</dt><dd>{v.is_free === true ? "Listed as free entry; check conditions with the venue" : v.price_text || "Check prices with the venue"}</dd></div>
      {!!v.facilities.length && <div><dt className="font-semibold">Listed facilities</dt><dd>{v.facilities.map(f => FACILITY_LABELS[f] ?? f.replace(/_/g," ")).join(", ")}</dd></div>}
    </dl><div className="mt-6 flex flex-wrap gap-4">{v.website_url && <a className="font-semibold underline" href={v.website_url} target="_blank" rel="noopener noreferrer">Venue website</a>}<a className="font-semibold underline" href={directionsUrl(v)} target="_blank" rel="noopener noreferrer">Directions</a></div></section></div>
    <p className="max-w-2xl text-sm text-muted-foreground">Visitor information may change. Confirm opening times, accessibility, suitability for your children and any charges with the venue before travelling. A directory listing does not imply independently verified child suitability.</p>
  </div>
}

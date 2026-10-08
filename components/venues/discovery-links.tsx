import Link from "next/link"
import { approvedDiscoveryPages } from "@/lib/venue-discovery"

export async function DiscoveryLinks() {
  const pages = await approvedDiscoveryPages()
  if (!pages.length) return null
  return <section aria-labelledby="browse-places-title" className="rounded-xl border bg-card p-5">
    <h2 id="browse-places-title" className="font-heading text-xl font-bold">Browse family days out by area</h2>
    <ul className="mt-3 flex flex-wrap gap-3">{pages.map(({ area, category }) => <li key={`${area.slug}-${category.slug}`}>
      <Link className="inline-block rounded-full border px-4 py-2 text-sm font-semibold hover:bg-muted" href={`/places/${area.slug}/${category.slug}`}>{category.name} in {area.name}</Link>
    </li>)}</ul>
  </section>
}

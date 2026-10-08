import coreSitemap from "@/lib/core-sitemap"
import { approvedDiscoveryPages } from "@/lib/venue-discovery"
import { isProduction, siteUrl } from "@/lib/seo"
import { COMING_SOON } from "@/lib/launch"
import { urlset, xmlHeaders } from "@/lib/sitemap-xml"
export const dynamic = "force-dynamic"
export async function GET() {
  if(!isProduction) return new Response(urlset([]),{headers:xmlHeaders})
  const base = await coreSitemap()
  const pages = COMING_SOON ? [] : await approvedDiscoveryPages()
  return new Response(urlset([...base,...pages.map(({area,category})=>({url:`${siteUrl}/places/${area.slug}/${category.slug}`}))]),{headers:xmlHeaders})
}

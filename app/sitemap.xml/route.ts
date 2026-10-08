import { siteUrl, isProduction } from "@/lib/seo"
import { xmlEscape, xmlHeaders } from "@/lib/sitemap-xml"
import { COMING_SOON } from "@/lib/launch"
export const dynamic = "force-dynamic"
export function GET() {
  const urls = [`${siteUrl}/sitemaps/core.xml`, ...(!COMING_SOON && isProduction ? Array.from("0123456789abcdef", shard => `${siteUrl}/sitemaps/venues/${shard}.xml`) : [])]
  return new Response(`<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${urls.map(url=>`<sitemap><loc>${xmlEscape(url)}</loc></sitemap>`).join("")}</sitemapindex>`, {headers:xmlHeaders})
}

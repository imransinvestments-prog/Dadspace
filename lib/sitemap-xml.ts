export function xmlEscape(value: string) {
  return value.replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&apos;"})[c]!)
}
export function urlset(entries: {url: string; lastModified?: string | Date}[]) {
  if (entries.length > 50000) throw new Error("Sitemap URL limit exceeded; split this shard")
  const xml = `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${entries.map(e=>`<url><loc>${xmlEscape(e.url)}</loc>${e.lastModified ? `<lastmod>${xmlEscape(e.lastModified instanceof Date ? e.lastModified.toISOString() : e.lastModified)}</lastmod>` : ""}</url>`).join("")}</urlset>`
  if (new TextEncoder().encode(xml).length > 50 * 1024 * 1024) throw new Error("Sitemap byte limit exceeded")
  return xml
}
export const xmlHeaders = {"Content-Type":"application/xml; charset=utf-8","Cache-Control":"no-store"}

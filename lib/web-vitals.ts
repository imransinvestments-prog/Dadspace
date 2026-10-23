// Field Core Web Vitals (#141). Vercel Hobby hides per-metric Speed Insights, so the
// site records its own. Rows hold the metric, page path and a coarse device class only:
// never an IP address, user agent, query string or account.

export const METRICS = ["LCP", "INP", "CLS", "FCP", "TTFB"] as const
const RATINGS = ["good", "needs-improvement", "poor"]
// Lab tools and crawlers are not visitors; counting them would distort field p75.
const NOT_A_VISITOR = /bot|crawl|spider|slurp|lighthouse|headless|pagespeed|gtmetrix|preview/i
const MOBILE = /mobi|android|iphone|ipod|ipad/i

export type VitalRow = {
  metric: (typeof METRICS)[number]
  value: number
  rating: string | null
  metric_id: string
  navigation_type: string | null
  route: string
  device: "mobile" | "desktop"
}

const text = (value: unknown, max: number) =>
  typeof value === "string" && value.length > 0 && value.length <= max ? value : null

export function parseVital(body: unknown, userAgent: string | null): VitalRow | null {
  if (!userAgent || NOT_A_VISITOR.test(userAgent) || !body || typeof body !== "object") return null
  const input = body as Record<string, unknown>
  const metric = METRICS.find(name => name === input.name)
  const value = input.value
  // CLS is unitless (normally below 1); the others are milliseconds. Ten minutes is not a page load.
  if (!metric || typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > (metric === "CLS" ? 100 : 600_000)) return null
  const metricId = text(input.id, 100)
  const route = text(input.route, 200)
  if (!metricId || !route || !route.startsWith("/") || /[?#\s]/.test(route)) return null
  const rating = text(input.rating, 20)
  return {
    metric,
    value,
    rating: rating && RATINGS.includes(rating) ? rating : null,
    metric_id: metricId,
    navigation_type: text(input.navigationType, 30),
    route: route.length > 1 ? route.replace(/\/+$/, "") || "/" : route,
    device: MOBILE.test(userAgent) ? "mobile" : "desktop",
  }
}

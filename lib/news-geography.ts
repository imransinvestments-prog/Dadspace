import geography from "../news_geography.json"

export const NEWS_LOCATION_VERSION = geography.version

/** Identical to the worker normalisation; only these tokens enter raw filters. */
export function newsSlug(value: unknown): string | null {
  if (typeof value !== "string" || /\(pseudo\)|unparished area/i.test(value)) return null
  const token = value.trim().toLowerCase().replace(/&/g, " and ").replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "")
  return token && token.length <= 100 ? token : null
}

export function newsArea(value: unknown): string | null {
  const token = newsSlug(value)
  if (!token) return null
  const cleaned = token.replace(/_(?:county_council|district_council|borough_council|city_council|council)$/, "")
  return (geography.areaAliases as Record<string, string>)[cleaned] ?? cleaned
}

export function newsGeoRegion(value: unknown): string | null {
  const token = newsSlug(value)
  if (!token) return null
  const canonical = (geography.regionAliases as Record<string, string>)[token] ?? token
  return geography.regions.includes(canonical) ? canonical : null
}

/** Persisted values must already be plain slugs; never interpolate raw input. */
export function isNewsToken(value: unknown): value is string | null | undefined {
  return value == null || (typeof value === "string" && value.length <= 100 && /^[a-z0-9]+(?:_[a-z0-9]+)*$/.test(value))
}

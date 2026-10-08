/*
 * Everything the News page needs to talk to the database.
 *
 * Safety rules:
 * - Uses ONLY the public "anon" key, the same key that's safe to show in a browser.
 * - Reads ONLY from the `feed_items` view, and only ever calls `select`, so nothing
 *   in the database can be changed from here.
 */
import { createClient, type SupabaseClient } from "@supabase/supabase-js"
import { isNewsToken, NEWS_LOCATION_VERSION, newsCounty, newsDistrict, newsGeoRegion } from "./news-geography"

/** How many articles to show at a time before the "Load more" button. */
export const PAGE_SIZE = 20

/** The columns we read from `feed_items`. We never read the full article text. */
const COLUMNS =
  "id,title,url,source_name,published_at,summary,why_it_matters,category,relevance,region,geo_scope,geo_region,admin_area,locality"

/** Region choices shown in the dropdown. "all" means no region filter. */
export const REGIONS = [
  { value: "all", label: "All UK" },
  { value: "england", label: "England" },
  { value: "scotland", label: "Scotland" },
  { value: "wales", label: "Wales" },
  { value: "northern_ireland", label: "Northern Ireland" },
] as const

/** Category chips, in the order they appear. "all" means no category filter. */
export const CATEGORIES = [
  { value: "all", label: "All" },
  { value: "money", label: "Money" },
  { value: "policy", label: "Policy" },
  { value: "safety", label: "Safety" },
  { value: "activities", label: "Activities" },
  { value: "parenting", label: "Parenting" },
  { value: "wellbeing", label: "Wellbeing" },
  { value: "health", label: "Health" },
  { value: "education", label: "Education" },
] as const

export type RegionFilter = (typeof REGIONS)[number]["value"]
export type CategoryFilter = (typeof CATEGORIES)[number]["value"]

export type NewsLocation = {
  version: number
  region: RegionFilter | null
  geoRegion?: string | null
  adminArea?: string | null
  locality?: string | null
}

/** One row from the `feed_items` view. */
export type NewsItem = {
  id: string
  title: string
  url: string | null
  source_name: string | null
  published_at: string | null
  summary: string | null
  why_it_matters: string | null
  category: string | null
  relevance: number | null
  region: string | null
  geo_scope: string | null
  geo_region: string | null
  admin_area: string | null
  locality: string | null
}

/** Friendly labels for badges, e.g. "northern_ireland" -> "Northern Ireland". */
export const REGION_LABELS: Record<string, string> = Object.fromEntries(REGIONS.map((r) => [r.value, r.label]))
export const CATEGORY_LABELS: Record<string, string> = {
  ...Object.fromEntries(CATEGORIES.map((c) => [c.value, c.label])),
  other: "Other",
}

/** Checks a value (e.g. one saved in the browser) is a real region choice. */
export function isRegion(value: unknown): value is RegionFilter {
  return REGIONS.some((r) => r.value === value)
}

/** Old ward-based locations expire once; malformed browser/API data is ignored. */
export function parseNewsLocation(value: unknown): NewsLocation | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null
  const row = value as Record<string, unknown>
  if (row.version !== NEWS_LOCATION_VERSION || !isRegion(row.region) || row.region === "all") return null
  if (![row.geoRegion, row.adminArea, row.locality].every(isNewsToken)) return null
  return {
    version: NEWS_LOCATION_VERSION,
    region: row.region,
    geoRegion: row.region === "england" ? newsGeoRegion(row.geoRegion) : null,
    adminArea: newsCounty(row.adminArea, row.region) ?? newsDistrict(row.adminArea, row.region),
    locality: newsDistrict(row.locality, row.region),
  }
}

/** Country/region guards stay outside every location match. */
export function newsLocationFilter(region: RegionFilter, input?: NewsLocation | null): string | null {
  if (region === "all") return null
  const location = parseNewsLocation(input)
  if (!location || location.region !== region || !(location.geoRegion || location.adminArea || location.locality)) {
    return `region.eq.uk,region.eq.${region}`
  }
  const matches = [
    "region.eq.uk",
    `and(region.eq.${region},geo_scope.eq.nationwide)`,
    `and(region.eq.${region},geo_scope.is.null)`,
  ]
  if (location.geoRegion) matches.push(`and(region.eq.${region},geo_scope.eq.regional,geo_region.eq.${location.geoRegion})`)
  if (location.locality) matches.push(`and(region.eq.${region},geo_scope.eq.local,locality.eq.${location.locality})`)
  // A named district takes precedence over county context on the story.
  // County-wide stories deliberately have no district/locality.
  if (location.adminArea) matches.push(`and(region.eq.${region},geo_scope.eq.local,locality.is.null,admin_area.eq.${location.adminArea})`)
  return matches.join(",")
}

let client: SupabaseClient | null = null

/** Creates the read-only database connection using the public anon key. */
function getNewsClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY
  if (!url || !anonKey) throw new Error("The Supabase URL or anon key is missing.")
  if (!client) {
    client = createClient(url, anonKey, { auth: { persistSession: false, autoRefreshToken: false } })
  }
  return client
}

/**
 * Fetches one page of articles (20 at a time), newest first.
 *
 * When precise location is available, the feed includes:
 * - UK-wide stories;
 * - nation-wide stories for the user's UK nation;
 * - regional/local stories matching the user's coarse region/admin area/locality.
 *
 * Rows created before locality metadata exists keep the old UK/nation behaviour so
 * rollout is backwards-compatible while the 14-day feed naturally refreshes.
 */
export async function fetchNews({
  region,
  category,
  page,
  location,
}: {
  region: RegionFilter
  category: CategoryFilter
  page: number
  location?: NewsLocation | null
}): Promise<NewsItem[]> {
  const from = page * PAGE_SIZE
  const to = from + PAGE_SIZE - 1

  let query = getNewsClient()
    .from("feed_items")
    .select(COLUMNS)
    .order("published_at", { ascending: false, nullsFirst: false })
    .range(from, to)

  if (category !== "all") query = query.eq("category", category)

  const filter = newsLocationFilter(region, location)
  if (filter) query = query.or(filter)

  const { data, error } = await query
  if (error) throw new Error(error.message)
  return (data ?? []).map((row) => ({ ...row, id: String(row.id) })) as NewsItem[]
}

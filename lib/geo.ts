import "server-only"
import { unstable_cache } from "next/cache"

export type Point = { lat: number; lng: number }
export type Locatable = { location: string | null; source_id?: string | null }

type Candidate = Point & { name?: string }

const MONTH = 60 * 60 * 24 * 30
const CLUSTER_KM = 40
const MEMO_TTL_MS = 60 * 60 * 1000
const MAX_OSM_LOOKUPS = 25
const USER_AGENT = "Dadspace/1.0 (+https://github.com/imransinvestments-prog/Dadspace)"

const POSTCODE = /\b([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})\b/i
const VAGUE = /\b(multiple venues|various|online|tbc|tba)\b/i
const VENUE_WORDS =
  /\b(library|venue hire|country park|national nature reserve|nature reserve|park|community (centre|hall|association)|church hall|church|hall|centre|castle|palace|gardens?|museum|hotel( and spa)?|farm|barns?|school|academy|primary|junior|high|stadium|studios?|leisure|sports?|tennis|club|fc|theatre|cinema|outdoor activity|outdoors|shopping|temple|boardwalk|woods?|civic|film|the|indoors)\b/gi
const WEAK_QUERIES = new Set(["new", "old", "the", "north", "south", "east", "west", "london", "essex"])

export function distanceKm(a: Point, b: Point) {
  const rad = Math.PI / 180
  const dLat = (b.lat - a.lat) * rad
  const dLng = (b.lng - a.lng) * rad
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLng / 2) ** 2
  return 2 * 6371 * Math.asin(Math.sqrt(h))
}

export const kmToMiles = (km: number) => km * 0.621371

async function getJson<T>(url: string): Promise<T | null> {
  const res = await fetch(url, {
    cache: "no-store",
    signal: AbortSignal.timeout(8000),
    headers: { "User-Agent": USER_AGENT, Accept: "application/json" },
  })
  if (res.status === 404) return null
  // Throwing (instead of returning null) keeps transient failures out of the cache.
  if (!res.ok) throw new Error(`Geocoder HTTP ${res.status}`)
  return (await res.json()) as T
}

type PostcodeResult = { result: { latitude: number | null; longitude: number | null } | null }

const lookupPostcode = unstable_cache(
  async (postcode: string): Promise<Point | null> => {
    const full = await getJson<PostcodeResult>(`https://api.postcodes.io/postcodes/${encodeURIComponent(postcode)}`)
    const hit = full?.result
    if (hit?.latitude != null && hit.longitude != null) return { lat: hit.latitude, lng: hit.longitude }

    const outward = postcode.slice(0, -3)
    const partial = await getJson<PostcodeResult>(`https://api.postcodes.io/outcodes/${encodeURIComponent(outward)}`)
    const area = partial?.result
    return area?.latitude != null && area.longitude != null ? { lat: area.latitude, lng: area.longitude } : null
  },
  ["geo-postcode-v1"],
  { revalidate: MONTH },
)

type PlacesResult = { result: { name_1: string; latitude: number | null; longitude: number | null }[] | null }

const lookupPlaces = unstable_cache(
  async (query: string): Promise<Candidate[]> => {
    const body = await getJson<PlacesResult>(`https://api.postcodes.io/places?limit=10&q=${encodeURIComponent(query)}`)
    return (body?.result ?? [])
      .filter((p) => p.latitude != null && p.longitude != null)
      .map((p) => ({ lat: p.latitude as number, lng: p.longitude as number, name: p.name_1 }))
  },
  ["geo-places-v1"],
  { revalidate: MONTH },
)

// Nominatim's usage policy allows at most one request per second.
let osmQueue: Promise<unknown> = Promise.resolve()
function throttled<T>(task: () => Promise<T>): Promise<T> {
  const run = osmQueue.then(task)
  osmQueue = run.catch(() => undefined).then(() => new Promise((r) => setTimeout(r, 1100)))
  return run
}

const lookupOsm = unstable_cache(
  async (query: string): Promise<Candidate[]> => {
    const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=gb&limit=5&q=${encodeURIComponent(query)}`
    const body = await throttled(() => getJson<{ lat: string; lon: string; name?: string }[]>(url))
    return (body ?? []).map((p) => ({ lat: Number(p.lat), lng: Number(p.lon), name: p.name }))
  },
  ["geo-osm-v1"],
  { revalidate: MONTH },
)

function tidy(text: string) {
  return text.replace(/[()]/g, " ").replace(/\s+/g, " ").trim().replace(/^[\s,.:-]+|[\s,.:-]+$/g, "")
}

function queriesFor(location: string) {
  const parts = location.split(/,| in |\/| - /i).map(tidy).filter(Boolean).reverse()
  const queries: { text: string; strict: boolean }[] = []
  for (const part of parts) {
    queries.push({ text: part, strict: false })
    const stripped = tidy(part.replace(VENUE_WORDS, " "))
    if (stripped && stripped.toLowerCase() !== part.toLowerCase()) queries.push({ text: stripped, strict: true })
  }
  return queries.filter((q) => q.text.length >= 3 && !WEAK_QUERIES.has(q.text.toLowerCase()) && !/^\d+$/.test(q.text))
}

function namesMatch(name: string | undefined, query: string) {
  if (!name) return false
  const n = name.toLowerCase()
  const q = query.toLowerCase()
  return n === q || n.startsWith(`${q}-`) || n.startsWith(`${q} `)
}

async function candidatesFor(location: string, osmBudget: { left: number }, strict = false): Promise<Candidate[]> {
  if (VAGUE.test(location)) return []
  const postcode = location.match(POSTCODE)
  if (postcode) {
    const point = await lookupPostcode(`${postcode[1]}${postcode[2]}`.toUpperCase())
    if (point) return [point]
  }

  for (const query of queriesFor(location)) {
    const places = await lookupPlaces(query.text)
    const exact = places.filter((p) => namesMatch(p.name, query.text))
    if (exact.length) return exact
    if (!strict && !query.strict && places.length && query.text.split(" ").length > 1) return places
  }

  if (strict || osmBudget.left <= 0) return []
  osmBudget.left -= 1
  return lookupOsm(location)
}

async function mapWithLimit<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const out = new Array<R>(items.length)
  let next = 0
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) {
      const i = next++
      out[i] = await fn(items[i])
    }
  })
  await Promise.all(workers)
  return out
}

export function locationKey(item: Locatable) {
  return `${item.source_id ?? ""}|${item.location ?? ""}`
}

/**
 * Picks, for each ambiguous place name, the candidate that sits closest to the
 * other venues from the same source (e.g. "Bampton" next to other Oxfordshire libraries).
 */
function resolveBySource(entries: { key: string; source: string; candidates: Candidate[] }[], strict = false) {
  const bySource = new Map<string, typeof entries>()
  for (const entry of entries) {
    if (!entry.candidates.length) continue
    const group = bySource.get(entry.source) ?? []
    group.push(entry)
    bySource.set(entry.source, group)
  }

  const resolved = new Map<string, Point>()
  for (const group of bySource.values()) {
    for (const entry of group) {
      let best = entry.candidates[0]
      if (entry.candidates.length > 1) {
        let bestScore = -1
        let tied = false
        for (const candidate of entry.candidates) {
          const score = group.filter(
            (other) => other !== entry && other.candidates.some((c) => distanceKm(candidate, c) < CLUSTER_KM),
          ).length
          if (score > bestScore) {
            best = candidate
            bestScore = score
            tied = false
          } else if (score === bestScore) {
            tied = true
          }
        }
        if (strict && (bestScore <= 0 || tied)) continue
      }
      resolved.set(entry.key, { lat: best.lat, lng: best.lng })
    }
  }
  return resolved
}

let memo: { signature: string; at: number; result: Promise<Map<string, Point>> } | null = null

/** Geocodes event venues without touching the database; results live in the Next.js cache. */
export function geocodeLocations(items: Locatable[], strict = false): Promise<Map<string, Point>> {
  const unique = new Map<string, { key: string; source: string; location: string }>()
  for (const item of items) {
    if (!item.location?.trim()) continue
    const key = locationKey(item)
    unique.set(key, { key, source: item.source_id ?? "", location: item.location.trim() })
  }
  const signature = `${strict}|${[...unique.keys()].sort().join("\n")}`
  if (memo && memo.signature === signature && Date.now() - memo.at < MEMO_TTL_MS) return memo.result

  const osmBudget = { left: MAX_OSM_LOOKUPS }
  const result = mapWithLimit([...unique.values()], 6, async (entry) => {
    try {
      return { ...entry, candidates: await candidatesFor(entry.location, osmBudget, strict) }
    } catch {
      return { ...entry, candidates: [] as Candidate[] }
    }
  }).then((entries) => resolveBySource(entries, strict))

  memo = { signature, at: Date.now(), result }
  result.catch(() => {
    memo = null
  })
  return result
}

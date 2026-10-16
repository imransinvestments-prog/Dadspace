export const DEFAULT_RADIUS_KM = 10
export const RADIUS_OPTIONS = [10, 25, 50, 100] as const
export type DiscoveryScope = 'local' | 'unknown' | 'online'

/** One public contract for discovery feeds; national browsing has no radius. */
export function parseDiscoveryRadius(params: URLSearchParams) {
  const raw = params.get('radiusKm')
  const radiusKm = raw === null ? DEFAULT_RADIUS_KM : Number(raw)
  const scope = params.get('scope') ?? 'local'
  if (!Number.isFinite(radiusKm) || radiusKm <= 0 || radiusKm > 100 || raw?.trim() === '') return null
  if (!['local', 'unknown', 'online'].includes(scope)) return null
  if ((raw !== null || params.has('scope')) && (!params.has('lat') || !params.has('lng'))) return null
  return { radiusKm, scope: scope as DiscoveryScope }
}

type Listing = { location: string | null; distance_miles?: number | null }
export function isOnlineListing(row: Listing) {
  return /\b(online|virtual|via zoom|zoom meeting)\b/i.test(row.location ?? '')
}

export function withinDiscoveryScope<T extends Listing>(rows: T[], radiusKm = DEFAULT_RADIUS_KM, scope: DiscoveryScope = 'local'): T[] {
  return rows.filter(row => {
    const online = isOnlineListing(row)
    if (scope === 'online') return online
    if (online) return false
    const distance = row.distance_miles
    const known = typeof distance === 'number' && Number.isFinite(distance) && distance >= 0
    if (scope === 'unknown') return !known
    return known && distance <= radiusKm / 1.609344
  })
}

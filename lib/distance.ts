export type Point = { lat: number; lng: number }

export function parsePoint(params: URLSearchParams): Point | null {
  const a = params.get('lat'), b = params.get('lng')
  if (!a?.trim() || !b?.trim()) return null
  const lat = Number(a), lng = Number(b)
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) return null
  return { lat: Math.round(lat * 100) / 100, lng: Math.round(lng * 100) / 100 }
}

export function nearestFirst<T extends { id: string; distance_miles?: number | null }>(items: T[], tie: (a: T,b: T) => number): T[] {
  const distance = (v: T) => typeof v.distance_miles === 'number' && Number.isFinite(v.distance_miles) ? v.distance_miles : Infinity
  return [...items].sort((a,b) => {
    const aa=distance(a), bb=distance(b)
    return (aa < bb ? -1 : aa > bb ? 1 : 0) || tie(a,b) || a.id.localeCompare(b.id)
  })
}

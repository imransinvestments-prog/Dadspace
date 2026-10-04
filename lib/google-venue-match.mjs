const normalize = value => String(value || '').normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim()
const tokens = value => normalize(value).split(' ').filter(t => t && !['the','and','of','at','uk'].includes(t))
const postcode = value => String(value || '').toUpperCase().replace(/\s/g, '')
export function distanceMeters(a, b) {
  if (![a?.latitude,a?.longitude,b?.latitude,b?.longitude].every(v => typeof v === 'number' && Number.isFinite(v))) return null
  if (Math.abs(a.latitude)>90 || Math.abs(b.latitude)>90 || Math.abs(a.longitude)>180 || Math.abs(b.longitude)>180) return null
  const rad = x => x * Math.PI / 180
  const h = Math.sin(rad(b.latitude-a.latitude)/2)**2 + Math.cos(rad(a.latitude))*Math.cos(rad(b.latitude))*Math.sin(rad(b.longitude-a.longitude)/2)**2
  return 6371000 * 2 * Math.asin(Math.min(1, Math.sqrt(h)))
}
export function searchableVenue(row) {
  const name = normalize(row.venue_name || row.venue_label)
  return !!name && !['closed','unknown','unnamed','funfair','playground','park','car park'].includes(name)
    && (row.postcode || row.town_city || (row.latitude != null && row.longitude != null))
}
export function matchVenue(row, places) {
  const name = row.venue_name || row.venue_label
  const expected = tokens(name)
  const large = /theme park|zoo|animal park|nature|country park/i.test(row.category || '')
  const matches = []
  for (const place of places) {
    if (!place.id || place.businessStatus === 'CLOSED_PERMANENTLY') continue
    const actual = new Set(tokens(place.displayName?.text))
    const overlap = expected.filter(t => actual.has(t)).length / Math.max(1,expected.length)
    if (overlap < .8 || (expected.length === 1 && !actual.has(expected[0]))) continue
    const components = place.addressComponents || []
    const pc = components.find(c => c.types?.includes('postal_code'))?.longText
    const samePostcode = !!row.postcode && postcode(pc) === postcode(row.postcode)
    const country = components.find(c => c.types?.includes('country'))?.shortText
    if (country !== 'GB') continue
    const distance = distanceMeters(row,place.location)
    // Matching postcode alone is only sufficient when source coordinates are absent.
    if (distance != null ? distance > (large ? 2000 : 300) : !samePostcode) continue
    matches.push({ placeId: place.id, distance, overlap, samePostcode })
  }
  // Multiple plausible businesses need human review; never just take result 1.
  const unique = [...new Map(matches.map(m => [m.placeId,m])).values()]
  return unique.length === 1 ? { status: 'matched', ...unique[0] } :
    { status: unique.length ? 'ambiguous' : 'no_match' }
}

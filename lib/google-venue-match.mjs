const normalize = value => String(value || '').normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim()
const tokens = value => normalize(value).split(' ').filter(t => t && !['the','and','of','at','uk'].includes(t))
const postcode = value => String(value || '').toUpperCase().replace(/\s/g, '')
export function isPlayground(row) {
  return /play\s*ground|play\s*park/i.test(String(row.category || '').replace(/[_-]/g,' '))
}
export function websiteIdentity(value) {
  try {
    const url=new URL(value)
    if (!['http:','https:'].includes(url.protocol) || url.username || url.password) return null
    const host=url.hostname.toLowerCase().replace(/^www\./,'')
    if (/(^|\.)(google\.[a-z.]+|goo\.gl|facebook\.com|instagram\.com|tripadvisor\.[a-z.]+)$/.test(host)) return null
    return {host,path:url.pathname.replace(/\/+$/,'').toLowerCase() || '/'}
  } catch { return null }
}
export function linkedPlaceId(row) {
  for (const value of [row.website,row.source_url]) {
    try {
      const url=new URL(value)
      if (!/(^|\.)google\.(com|co\.uk)$/.test(url.hostname) || !url.pathname.startsWith('/maps')) continue
      const id=url.searchParams.get('query_place_id') || url.searchParams.get('q')?.match(/^place_id:([A-Za-z0-9_-]+)$/)?.[1]
      if (id && /^[A-Za-z0-9_-]{10,255}$/.test(id)) return id
    } catch { /* Website may be absent or not a complete URL. */ }
  }
  return null
}
export function venueSearchBody(row) {
  const address=row.address || [row.address_line_1,row.address_line_2].filter(Boolean).join(', ')
  const textQuery=[...new Set([row.venue_name || row.venue_label,row.postcode || row.town_city || address,'United Kingdom'].filter(Boolean))].join(', ')
  const body={textQuery,regionCode:'GB',languageCode:'en',pageSize:5}
  if (distanceMeters(row,row)===0) body.locationBias={circle:{center:{latitude:row.latitude,longitude:row.longitude},radius:2500}}
  return body
}
export function distanceMeters(a, b) {
  if (![a?.latitude,a?.longitude,b?.latitude,b?.longitude].every(v => typeof v === 'number' && Number.isFinite(v))) return null
  if (Math.abs(a.latitude)>90 || Math.abs(b.latitude)>90 || Math.abs(a.longitude)>180 || Math.abs(b.longitude)>180) return null
  const rad = x => x * Math.PI / 180
  const h = Math.sin(rad(b.latitude-a.latitude)/2)**2 + Math.cos(rad(a.latitude))*Math.cos(rad(b.latitude))*Math.sin(rad(b.longitude-a.longitude)/2)**2
  return 6371000 * 2 * Math.asin(Math.min(1, Math.sqrt(h)))
}
export function searchableVenue(row) {
  const name = normalize(row.venue_name || row.venue_label)
  const identity=linkedPlaceId(row) || (!!name && !['closed','unknown','unnamed','funfair','playground','park','car park'].includes(name))
  return Boolean(!row.image_url && !isPlayground(row) && identity
    && (row.postcode || row.town_city || (row.latitude != null && row.longitude != null)))
}
export function matchVenue(row, places) {
  if (row.image_url || isPlayground(row)) return {status:row.image_url?'already_has_photo':'excluded_playground'}
  const name = row.venue_name || row.venue_label
  const expected = tokens(name)
  const large = /theme park|zoo|animal park|nature|country park/i.test(row.category || '')
  const matches = []
  const expectedWebsite=websiteIdentity(row.website)
  const expectedId=linkedPlaceId(row)
  const rejected={}
  const reject=reason=>{rejected[reason]=(rejected[reason]||0)+1}
  for (const place of places) {
    if (!place.id || place.businessStatus === 'CLOSED_PERMANENTLY') {reject('closed_or_missing_id');continue}
    const actual = new Set(tokens(place.displayName?.text))
    const overlap = expected.filter(t => actual.has(t)).length / Math.max(1,expected.length)
    const components = place.addressComponents || []
    const pc = components.find(c => c.types?.includes('postal_code'))?.longText
    const samePostcode = !!row.postcode && postcode(pc) === postcode(row.postcode)
    const country = components.find(c => c.types?.includes('country'))?.shortText
    if (country !== 'GB') {reject('outside_uk');continue}
    const distance = distanceMeters(row,place.location)
    // Matching postcode alone is only sufficient when source coordinates are absent.
    if (distance != null ? distance > (large ? 2000 : 300) : !samePostcode) {reject('location_mismatch');continue}
    const candidateWebsite=websiteIdentity(place.websiteUri)
    const sameHost=!!expectedWebsite && expectedWebsite.host===candidateWebsite?.host
    const sameBranchUrl=sameHost && expectedWebsite.path!=='/' && expectedWebsite.path===candidateWebsite.path
    const nameMatches=overlap>=.8
    const knownId=!!expectedId && expectedId===place.id
    // A shared chain homepage alone cannot identify a branch. A matching
    // branch URL or linked place ID can handle a renamed venue, with location.
    const websiteMatches=sameBranchUrl || (sameHost && overlap>=.5 && (samePostcode || (distance!=null && distance<=300)))
    if (!knownId && !nameMatches && !websiteMatches) {reject('identity_mismatch');continue}
    const method=knownId?'linked_place_id_location':websiteMatches?'website_location':'name_location'
    matches.push({ placeId: place.id, distance, overlap, samePostcode, method })
  }
  // Multiple plausible businesses need human review; never just take result 1.
  const unique = [...new Map(matches.map(m => [m.placeId,m])).values()]
  return unique.length === 1 ? { status: 'matched', ...unique[0] } :
    { status: unique.length ? 'ambiguous' : 'no_match', reasons:rejected }
}

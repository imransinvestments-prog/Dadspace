const normalize = value => String(value || '').normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
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
  for (const value of [row.google_maps_url,row.maps_url,row.website,row.source_url,row.additional_source_url]) {
    try {
      const url=new URL(value)
      const host=url.hostname.toLowerCase()
      const googleHost = host === 'google.com' || host.endsWith('.google.com') || host === 'google.co.uk' || host.endsWith('.google.co.uk')
      if (!googleHost || !url.pathname.startsWith('/maps')) continue
      const id=url.searchParams.get('query_place_id') || url.searchParams.get('q')?.match(/^place_id:([A-Za-z0-9_-]+)$/)?.[1]
      if (id && /^[A-Za-z0-9_-]{10,255}$/.test(id)) return id
    } catch { /* Optional URLs may be absent or malformed. */ }
  }
  return null
}

export function categoryPlaceTypes(category) {
  const value=normalize(category)
  if (!value) return []
  if (/\blibrary\b/.test(value)) return ['library']
  if (/\bmuseum\b/.test(value)) return ['museum','art_museum','history_museum']
  if (/\baquarium\b/.test(value)) return ['aquarium']
  if (/\bwater park\b/.test(value)) return ['water_park']
  if (/\btheme park\b|\bamusement park\b/.test(value)) return ['amusement_park']
  if (/\bzoo\b|\banimal park\b|\bwildlife park\b/.test(value)) return ['zoo','wildlife_park']
  if (/\barcade\b/.test(value)) return ['video_arcade','amusement_center']
  if (/soft play|indoor play/.test(value)) return ['indoor_playground','amusement_center']
  if (/trampoline/.test(value)) return ['sports_complex','amusement_center','adventure_sports_center']
  return []
}

export function validCoordinates(row) {
  return [row?.latitude,row?.longitude].every(v => typeof v === 'number' && Number.isFinite(v))
    && Math.abs(row.latitude) <= 90 && Math.abs(row.longitude) <= 180
}

export function venueSearchRequest(row) {
  if (validCoordinates(row)) {
    const types=categoryPlaceTypes(row.category)
    const body={
      maxResultCount:20,
      rankPreference:'DISTANCE',
      locationRestriction:{circle:{center:{latitude:row.latitude,longitude:row.longitude},radius:2500}},
    }
    if (types.length) body.includedTypes=types
    return {path:'places:searchNearby',body}
  }
  const address=row.address || [row.address_line_1,row.address_line_2,row.town_city].filter(Boolean).join(', ')
  const location=[row.postcode,address,'United Kingdom'].filter(Boolean).join(', ')
  const category=normalize(row.category).replace(/_/g,' ')
  return {
    path:'places:searchText',
    body:{textQuery:[category,location].filter(Boolean).join(', '),regionCode:'GB',languageCode:'en',pageSize:10},
  }
}

export function venueSearchBody(row) {
  return venueSearchRequest(row).body
}

export function distanceMeters(a, b) {
  if (![a?.latitude,a?.longitude,b?.latitude,b?.longitude].every(v => typeof v === 'number' && Number.isFinite(v))) return null
  if (Math.abs(a.latitude)>90 || Math.abs(b.latitude)>90 || Math.abs(a.longitude)>180 || Math.abs(b.longitude)>180) return null
  const rad = x => x * Math.PI / 180
  const h = Math.sin(rad(b.latitude-a.latitude)/2)**2 + Math.cos(rad(a.latitude))*Math.cos(rad(b.latitude))*Math.sin(rad(b.longitude-a.longitude)/2)**2
  return 6371000 * 2 * Math.asin(Math.min(1, Math.sqrt(h)))
}

export function searchableVenue(row) {
  const hasLocation = validCoordinates(row) || !!postcode(row.postcode) || !!String(row.address || row.address_line_1 || '').trim()
  return Boolean(!row.image_url && !isPlayground(row) && (linkedPlaceId(row) || hasLocation))
}

function placePostcode(place) {
  const component=(place.addressComponents || []).find(c => c.types?.includes('postal_code'))
  return postcode(component?.longText || component?.shortText)
}

function placeCountry(place) {
  const component=(place.addressComponents || []).find(c => c.types?.includes('country'))
  return String(component?.shortText || '').toUpperCase()
}

function placeTypesMatch(row, place) {
  const expected=categoryPlaceTypes(row.category)
  if (!expected.length) return true
  const actual=new Set([...(place.types || []),place.primaryType].filter(Boolean))
  return expected.some(type => actual.has(type))
}

export function matchVenue(row, places) {
  if (row.image_url || isPlayground(row)) return {status:row.image_url?'already_has_photo':'excluded_playground'}
  const expectedId=linkedPlaceId(row)
  const expectedPostcode=postcode(row.postcode)
  const hasCoords=validCoordinates(row)
  const large=/theme park|zoo|animal park|wildlife park|water park/i.test(String(row.category || ''))
  const maxDistance=large ? 1500 : 150
  const closeDistance=large ? 500 : 50
  const expectedWebsite=websiteIdentity(row.website)
  const matches=[]
  const rejected={}
  const reject=reason=>{rejected[reason]=(rejected[reason]||0)+1}

  for (const place of places) {
    if (!place?.id || place.businessStatus === 'CLOSED_PERMANENTLY') {reject('closed_or_missing_id');continue}
    const country=placeCountry(place)
    if (country && country !== 'GB') {reject('outside_uk');continue}
    const candidatePostcode=placePostcode(place)
    const samePostcode=!!expectedPostcode && !!candidatePostcode && expectedPostcode===candidatePostcode
    const distance=distanceMeters(row,place.location)

    if (expectedId) {
      if (place.id !== expectedId) {reject('place_id_mismatch');continue}
      if (hasCoords && distance != null && distance > maxDistance) {reject('location_mismatch');continue}
      if (expectedPostcode && candidatePostcode && !samePostcode && !(distance != null && distance <= closeDistance)) {reject('postcode_mismatch');continue}
      matches.push({placeId:place.id,distance,samePostcode,method:'google_place_id'})
      continue
    }

    if (!placeTypesMatch(row,place)) {reject('type_mismatch');continue}
    if (hasCoords) {
      if (distance == null || distance > maxDistance) {reject('location_mismatch');continue}
      if (expectedPostcode && candidatePostcode && !samePostcode && distance > closeDistance) {reject('postcode_mismatch');continue}
    } else if (expectedPostcode) {
      if (!samePostcode) {reject('postcode_mismatch');continue}
    } else {
      reject('insufficient_identifier');continue
    }

    const candidateWebsite=websiteIdentity(place.websiteUri)
    const exactBranchWebsite=!!expectedWebsite && expectedWebsite.path!=='/' && expectedWebsite.host===candidateWebsite?.host && expectedWebsite.path===candidateWebsite?.path
    const method=hasCoords && samePostcode ? 'coordinates_postcode' : hasCoords ? 'coordinates' : 'postcode'
    matches.push({placeId:place.id,distance,samePostcode,exactBranchWebsite,method})
  }

  const unique=[...new Map(matches.map(m=>[m.placeId,m])).values()]
  if (unique.length===1) return {status:'matched',...unique[0]}
  if (unique.length>1) {
    const branchMatches=unique.filter(m=>m.exactBranchWebsite)
    if (branchMatches.length===1) return {status:'matched',...branchMatches[0],method:`${branchMatches[0].method}_website_branch`}
    return {status:'ambiguous',reasons:{...rejected,multiple_identifier_matches:unique.length}}
  }
  return {status:'no_match',reasons:rejected}
}

// Place IDs are durable. Photo names, image URLs and author details are fetched
// on demand and never written to the database or a persistent cache.
export const PLACE_ID = /^[A-Za-z0-9_-]{10,255}$/
export const PHOTO_MARKER = 'google-places:'
export function googlePlaceId(value) {
  if (typeof value !== 'string' || !value.startsWith(PHOTO_MARKER)) return null
  const id = value.slice(PHOTO_MARKER.length)
  return PLACE_ID.test(id) ? id : null
}
export function googleApiKey(env = process.env) {
  return env.GOOGLE_PLACES_API_KEY || env.GCP_API_KEY_2 || env.GCP_API_KEY
}
export class PlacesError extends Error {
  constructor(status) { super(`Google Places returned HTTP ${status}`); this.status = status }
}
export async function placesJson(path, { apiKey, fields, body, fetcher = fetch }) {
  const response = await fetcher(`https://places.googleapis.com/v1/${path}`, {
    method: body ? 'POST' : 'GET',
    headers: { 'X-Goog-Api-Key': apiKey, ...(fields ? { 'X-Goog-FieldMask': fields } : {}), ...(body ? { 'Content-Type': 'application/json' } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
    cache: 'no-store', signal: AbortSignal.timeout(15000),
  })
  if (!response.ok) throw new PlacesError(response.status)
  return response.json()
}
export function safeGoogleUrl(value, image = false) {
  try {
    const url = new URL(value.startsWith('//') ? `https:${value}` : value)
    const host = url.hostname
    const allowed = image ? host.endsWith('.googleusercontent.com') :
      host === 'google.com' || host.endsWith('.google.com') || host === 'maps.app.goo.gl'
    return url.protocol === 'https:' && !url.username && !url.password && allowed ? url.href : null
  } catch { return null }
}
export async function fetchVenuePhoto(placeId, apiKey, fetcher = fetch) {
  if (!PLACE_ID.test(placeId)) return null
  const place = await placesJson(`places/${placeId}`, { apiKey, fields: 'photos', fetcher })
  const photo = place.photos?.[0]
  if (!photo || !new RegExp(`^places/${placeId}/photos/[A-Za-z0-9_-]+$`).test(photo.name)) return null
  const media = await placesJson(`${photo.name}/media?maxWidthPx=800&skipHttpRedirect=true`, { apiKey, fetcher })
  const imageUrl = safeGoogleUrl(media.photoUri, true)
  const sourceUrl = safeGoogleUrl(photo.googleMapsUri)
  // Keep the direct source-photo link, rather than substituting a venue link.
  if (!imageUrl || !sourceUrl) return null
  return {
    imageUrl, sourceUrl,
    authors: (photo.authorAttributions || []).map(a => ({
      name: String(a.displayName || 'Photo contributor'),
      uri: safeGoogleUrl(a.uri), avatar: safeGoogleUrl(a.photoUri, true),
    })),
  }
}

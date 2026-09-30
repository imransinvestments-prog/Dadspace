export type Venue = {
  id: string
  name: string
  category: string | null
  description: string | null
  address: string | null
  town: string | null
  postcode: string | null
  region: string | null
  latitude: number | null
  longitude: number | null
  website_url: string | null
  phone: string | null
  opening_hours: string | null
  price_text: string | null
  is_free: boolean | null
  age_range: string | null
  indoor: boolean | null
  outdoor: boolean | null
  facilities: string[]
  image_url: string | null
}

export const CATEGORY_LABELS: Record<string, string> = {
  soft_play: "Soft play",
  park: "Park & playground",
  farm: "Farm & animals",
  museum: "Museum",
  library: "Library",
  leisure: "Leisure & sport",
  attraction: "Attraction",
  cafe: "Family café",
  nature: "Nature & walks",
}

export const FACILITY_LABELS: Record<string, string> = {
  baby_changing: "Baby changing",
  parking: "Parking",
  cafe: "Café",
  accessible: "Step-free access",
  dog_friendly: "Dog friendly",
  toilets: "Toilets",
  pram_friendly: "Pram friendly",
}

export function categoryLabel(category: string | null) {
  if (!category) return "Venue"
  return CATEGORY_LABELS[category] ?? category.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase())
}

export function venueImage(venue: Venue) {
  if (venue.image_url) return venue.image_url
  switch (venue.category) {
    case "soft_play":
    case "cafe":
      return "/images/event-crafts.png"
    case "museum":
    case "library":
      return "/images/event-story.png"
    case "leisure":
      return "/images/event-sport.png"
    default:
      return "/images/event-outdoor.png"
  }
}

export function milesBetween(a: { lat: number; lng: number }, b: { lat: number; lng: number }) {
  const rad = Math.PI / 180
  const dLat = (b.lat - a.lat) * rad
  const dLng = (b.lng - a.lng) * rad
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLng / 2) ** 2
  return 2 * 3958.8 * Math.asin(Math.sqrt(h))
}

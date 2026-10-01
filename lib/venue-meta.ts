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
  image_source_url?: string | null
  image_attribution?: string | null
  image_license?: string | null
  image_license_url?: string | null
  image_title?: string | null
  image_credit?: string | null
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

type CategoryTheme = { match: RegExp; label: string; plural: string; image: string }

const CATEGORY_THEMES: CategoryTheme[] = [
  { match: /soft_play|indoor/, label: "Soft play", plural: "Soft play", image: "/images/venues/soft-play.png" },
  { match: /museum/, label: "Museum", plural: "Museums", image: "/images/venues/museum.png" },
  { match: /arcade/, label: "Arcade", plural: "Arcades", image: "/images/venues/arcade.png" },
  { match: /zoo|animal|farm/, label: "Zoo & animals", plural: "Zoos & animals", image: "/images/venues/zoo.png" },
  { match: /water_park|swim|leisure/, label: "Water park", plural: "Water parks", image: "/images/venues/water-park.png" },
  { match: /theme_park|attraction/, label: "Theme park", plural: "Theme parks", image: "/images/venues/theme-park.png" },
  { match: /playground|park$|^park/, label: "Playground", plural: "Playgrounds", image: "/images/venues/playground.png" },
  { match: /trampoline/, label: "Trampolines", plural: "Trampolines", image: "/images/venues/trampoline.png" },
  { match: /aquarium/, label: "Aquarium", plural: "Aquariums", image: "/images/venues/aquarium.png" },
  { match: /library/, label: "Library", plural: "Libraries", image: "/images/event-story.png" },
  { match: /nature|walk/, label: "Nature & walks", plural: "Nature & walks", image: "/images/event-outdoor.png" },
]

function themeFor(category: string | null) {
  if (!category) return null
  return CATEGORY_THEMES.find((t) => t.match.test(category)) ?? null
}

export function categoryLabel(category: string | null) {
  if (!category) return "Venue"
  return (
    themeFor(category)?.label ??
    CATEGORY_LABELS[category] ??
    category.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase())
  )
}

export function categoryPlural(category: string) {
  return themeFor(category)?.plural ?? categoryLabel(category)
}

export function categoryImage(category: string | null) {
  return themeFor(category)?.image ?? "/images/event-outdoor.png"
}

export function venueImage(venue: Venue) {
  return venuePhotoUrl(venue) || categoryImage(venue.category)
}

export function venuePhotoUrl(venue: Venue): string | null {
  if (!venue.image_url || !venue.image_attribution || !venue.image_license) return null
  try {
    const image = new URL(venue.image_url)
    const source = new URL(venue.image_source_url ?? "")
    const licence = new URL(venue.image_license_url ?? "")
    const commonsImage = ["upload.wikimedia.org", "thumb.wikimedia.org"].includes(image.hostname)
    const storedImage = image.hostname === "ebebkbrdqmceckmhlcpw.supabase.co"
      && /^\/storage\/v1\/object\/public\/venue-images\/[0-9a-f-]{36}\/[0-9a-f]{16}\.webp$/.test(image.pathname)
    if (image.protocol !== "https:" || image.username || image.password || image.port || (!commonsImage && !storedImage)) return null
    if (source.protocol !== "https:" || source.hostname !== "commons.wikimedia.org") return null
    if (licence.protocol !== "https:" || licence.hostname !== "creativecommons.org") return null
    return image.href
  } catch { return null }
}

export function milesBetween(a: { lat: number; lng: number }, b: { lat: number; lng: number }) {
  const rad = Math.PI / 180
  const dLat = (b.lat - a.lat) * rad
  const dLng = (b.lng - a.lng) * rad
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * rad) * Math.cos(b.lat * rad) * Math.sin(dLng / 2) ** 2
  return 2 * 3958.8 * Math.asin(Math.sqrt(h))
}

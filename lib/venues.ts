import "server-only"
import { getSupabase } from "@/lib/supabase"
import type { Venue } from "@/lib/venue-meta"

export type VenuesResult = { venues: Venue[]; isPreview: boolean }

type Row = Record<string, unknown>

const str = (v: unknown) => (typeof v === "string" && v.trim() ? v.trim() : null)
const num = (v: unknown) => {
  const n = typeof v === "number" ? v : typeof v === "string" ? Number.parseFloat(v) : Number.NaN
  return Number.isFinite(n) ? n : null
}
const bool = (v: unknown) => (typeof v === "boolean" ? v : null)

function list(v: unknown): string[] {
  if (Array.isArray(v)) return v.filter((x): x is string => typeof x === "string")
  if (typeof v === "string") return v.split(",").map((s) => s.trim()).filter(Boolean)
  return []
}

// OSM-style `fee` values are usually "yes"/"no"; anything else is treated as price text.
function feeInfo(fee: string | null): { is_free: boolean | null; price_text: string | null } {
  if (!fee) return { is_free: null, price_text: null }
  const f = fee.toLowerCase()
  if (f === "no" || f === "free") return { is_free: true, price_text: null }
  if (f === "yes") return { is_free: false, price_text: null }
  return { is_free: null, price_text: fee }
}

// Maps the `venues` table (venue_name, town_city, country, website, fee…) with fallbacks for older column names.
export function toVenue(row: Row): Venue | null {
  const name = str(row.venue_name) ?? str(row.venue_label) ?? str(row.name)
  if (!name) return null
  const fee = feeInfo(str(row.fee))
  const addressLines = [str(row.address_line_1), str(row.address_line_2)].filter(Boolean).join(", ")
  return {
    id: String(row.id ?? name),
    name,
    category: str(row.category)?.toLowerCase().replace(/[\s&-]+/g, "_") ?? null,
    description: str(row.description),
    address: str(row.address) ?? (addressLines || null),
    town: str(row.town_city) ?? str(row.town) ?? str(row.city) ?? str(row.nearby_settlement),
    postcode: str(row.postcode),
    region: str(row.country) ?? str(row.region),
    latitude: num(row.latitude ?? row.lat),
    longitude: num(row.longitude ?? row.lng ?? row.lon),
    website_url: str(row.website) ?? str(row.website_url) ?? str(row.url),
    phone: str(row.phone),
    opening_hours: str(row.opening_hours),
    price_text: str(row.price_text) ?? fee.price_text,
    is_free: bool(row.is_free) ?? fee.is_free,
    age_range: str(row.age_range),
    indoor: bool(row.indoor),
    outdoor: bool(row.outdoor),
    facilities: list(row.facilities),
    image_url: str(row.image_url),
    image_source_url: str(row.image_source_url),
    image_attribution: str(row.image_attribution),
    image_license: str(row.image_license),
    image_license_url: str(row.image_license_url),
    image_title: str(row.image_title),
    image_credit: str(row.image_credit),
  }
}

/** Read-only: selects from `venues`. Falls back to labelled preview venues until the table exists and has rows. */
export async function fetchVenues(): Promise<VenuesResult> {
  const supabase = getSupabase()
  if (supabase) {
    const { data, error } = await supabase.from("venues").select("*").eq("public_visible", true).order("venue_name").limit(500)
    if (error) console.error("Failed to load venues:", error.message)
    if (!error && data?.length) {
      const venues = (data as Row[]).map(toVenue).filter((v): v is Venue => v !== null)
      if (venues.length) return { venues, isPreview: false }
    }
  }
  return { venues: PREVIEW_VENUES, isPreview: true }
}

const base = {
  description: null,
  address: null,
  region: "England",
  phone: null,
  image_url: null,
} satisfies Partial<Venue>

const PREVIEW_VENUES: Venue[] = [
  {
    ...base,
    id: "p1",
    name: "Jungle Jim's Soft Play",
    category: "soft_play",
    description: "Three-tier climbing frame, separate under-3s zone and a café with a view of the action.",
    town: "Manchester",
    postcode: "M4 4BF",
    latitude: 53.4839,
    longitude: -2.2366,
    website_url: null,
    opening_hours: "Daily 9:30am – 6pm",
    price_text: "£6.50 per child",
    is_free: false,
    age_range: "0–10",
    indoor: true,
    outdoor: false,
    facilities: ["baby_changing", "cafe", "parking", "toilets"],
  },
  {
    ...base,
    id: "p2",
    name: "Heaton Park",
    category: "park",
    description: "Huge park with an adventure playground, boating lake and a small animal centre.",
    town: "Manchester",
    postcode: "M25 2SW",
    latitude: 53.5335,
    longitude: -2.2507,
    website_url: null,
    opening_hours: "Dawn to dusk",
    price_text: null,
    is_free: true,
    age_range: "All ages",
    indoor: false,
    outdoor: true,
    facilities: ["parking", "cafe", "toilets", "dog_friendly", "pram_friendly"],
  },
  {
    ...base,
    id: "p3",
    name: "Science and Industry Museum",
    category: "museum",
    description: "Hands-on galleries, working engines and weekend family workshops.",
    town: "Manchester",
    postcode: "M3 4FP",
    latitude: 53.4771,
    longitude: -2.2546,
    website_url: null,
    opening_hours: "Wed – Sun 10am – 5pm",
    price_text: null,
    is_free: true,
    age_range: "3+",
    indoor: true,
    outdoor: false,
    facilities: ["baby_changing", "accessible", "cafe", "toilets"],
  },
  {
    ...base,
    id: "p4",
    name: "Mudchute Farm",
    category: "farm",
    description: "City farm with goats, llamas and pigs, plus a riding school and nursery café.",
    town: "London",
    postcode: "E14 3HP",
    latitude: 51.4903,
    longitude: -0.0115,
    website_url: null,
    opening_hours: "Tue – Sun 9am – 4pm",
    price_text: null,
    is_free: true,
    age_range: "All ages",
    indoor: false,
    outdoor: true,
    facilities: ["cafe", "toilets", "pram_friendly", "dog_friendly"],
  },
  {
    ...base,
    id: "p5",
    name: "Splash Leisure Centre",
    category: "leisure",
    description: "Learner pool with wave machine sessions and family swim on weekend mornings.",
    town: "Birmingham",
    postcode: "B5 4BU",
    latitude: 52.4762,
    longitude: -1.8906,
    website_url: null,
    opening_hours: "Mon – Sun 7am – 9pm",
    price_text: "From £4 per child",
    is_free: false,
    age_range: "0+",
    indoor: true,
    outdoor: false,
    facilities: ["baby_changing", "parking", "accessible", "toilets"],
  },
  {
    ...base,
    id: "p6",
    name: "Central Library Rhyme Time",
    category: "library",
    description: "Free rhyme and story sessions in the children's library, plus a big picture book corner.",
    town: "Leeds",
    postcode: "LS1 3AB",
    latitude: 53.8006,
    longitude: -1.5491,
    website_url: null,
    opening_hours: "Mon – Sat 9am – 5pm",
    price_text: null,
    is_free: true,
    age_range: "0–5",
    indoor: true,
    outdoor: false,
    facilities: ["baby_changing", "accessible", "toilets", "pram_friendly"],
  },
  {
    ...base,
    id: "p7",
    name: "Pollok Country Park",
    category: "nature",
    description: "Woodland trails, Highland cattle and a big natural play area.",
    town: "Glasgow",
    postcode: "G43 1AT",
    region: "Scotland",
    latitude: 55.8284,
    longitude: -4.3137,
    website_url: null,
    opening_hours: "Always open",
    price_text: null,
    is_free: true,
    age_range: "All ages",
    indoor: false,
    outdoor: true,
    facilities: ["parking", "cafe", "dog_friendly", "toilets"],
  },
  {
    ...base,
    id: "p8",
    name: "Techniquest",
    category: "attraction",
    description: "Interactive science centre with a planetarium and live science shows.",
    town: "Cardiff",
    postcode: "CF10 5BW",
    region: "Wales",
    latitude: 51.4637,
    longitude: -3.1644,
    website_url: null,
    opening_hours: "Daily 10am – 5pm",
    price_text: "£12 adult, £10 child",
    is_free: false,
    age_range: "4+",
    indoor: true,
    outdoor: false,
    facilities: ["baby_changing", "accessible", "cafe", "toilets"],
  },
]

import "server-only"
import type { Venue } from "@/lib/venue-meta"


type Row = Record<string, unknown>

const str = (v: unknown) => (typeof v === "string" && v.trim() ? v.trim() : null)
const num = (v: unknown) => {
  const n = typeof v === "number" ? v : typeof v === "string" ? Number.parseFloat(v) : Number.NaN
  return Number.isFinite(n) ? n : null
}
const bool = (v: unknown) => (typeof v === "boolean" ? v : null)
function publicLink(value: unknown) {
  const raw = str(value)
  if (!raw) return null
  try { const url = new URL(raw); return ["https:","http:"].includes(url.protocol) && !url.username && !url.password ? url.href : null } catch { return null }
}

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
    website_url: publicLink(row.website ?? row.website_url ?? row.url),
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

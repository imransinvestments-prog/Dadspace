export function venueSlug(venue: { id: string; name: string }) {
  const label = venue.name.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80).replace(/-$/g, "") || "venue"
  return `${label}--${venue.id}`
}
export function venueIdFromSlug(slug: string): string | null {
  return /--([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$/i.exec(slug)?.[1].toLowerCase() ?? null
}
export function browsePage(value: string | string[] | undefined) {
  if (value === undefined) return 1
  return typeof value === "string" && /^[1-9]\d{0,3}$/.test(value) ? Number(value) : null
}

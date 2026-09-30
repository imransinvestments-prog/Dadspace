import Image from "next/image"
import { Accessibility, Baby, Clock, Coffee, Dog, Globe, MapPin, Navigation, Phone, SquareParking, type LucideIcon } from "lucide-react"
import { FACILITY_LABELS, categoryLabel, venueImage, type Venue } from "@/lib/venue-meta"

const FACILITY_ICONS: Record<string, LucideIcon> = {
  baby_changing: Baby,
  parking: SquareParking,
  cafe: Coffee,
  accessible: Accessibility,
  dog_friendly: Dog,
}

function formatMiles(miles: number) {
  if (miles < 1) return "Under a mile"
  const rounded = Math.round(miles)
  return `${rounded} ${rounded === 1 ? "mile" : "miles"}`
}

function setting(venue: Venue) {
  if (venue.indoor && venue.outdoor) return "Indoor & outdoor"
  if (venue.indoor) return "Indoor"
  if (venue.outdoor) return "Outdoor"
  return null
}

export function VenueCard({ venue, distance, index = 0 }: { venue: Venue; distance: number | null; index?: number }) {
  const image = venueImage(venue)
  const place = [venue.town, venue.postcode].filter(Boolean).join(", ") || venue.address
  const where = setting(venue)

  return (
    <article
      className="animate-rise flex h-full flex-col overflow-hidden rounded-lg border bg-card text-card-foreground"
      style={{ animationDelay: `${Math.min(index, 8) * 60}ms` }}
    >
      <div className="relative aspect-[16/9] overflow-hidden">
        <Image
          src={image || "/placeholder.svg"}
          alt=""
          fill
          unoptimized={image.startsWith("http")}
          sizes="(min-width: 1280px) 30vw, (min-width: 640px) 50vw, 100vw"
          className="object-cover"
        />
        <span className="absolute top-3 left-3 rounded-full bg-card px-3 py-1 text-xs font-bold text-card-foreground">
          {categoryLabel(venue.category)}
        </span>
        {venue.is_free ? (
          <span className="absolute top-3 right-3 rounded-full bg-highlight px-3 py-1 text-xs font-bold text-highlight-foreground">
            Free entry
          </span>
        ) : venue.price_text ? (
          <span className="absolute top-3 right-3 rounded-full bg-navy px-3 py-1 text-xs font-bold text-navy-foreground">
            {venue.price_text}
          </span>
        ) : null}
        {distance != null && (
          <span className="absolute bottom-3 left-3 flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-xs font-bold text-primary-foreground">
            <Navigation className="size-3" aria-hidden />
            {formatMiles(distance)}
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex flex-col gap-1">
          <h2 className="font-heading text-lg leading-snug font-bold text-pretty">{venue.name}</h2>
          {venue.description && <p className="line-clamp-2 text-sm leading-relaxed text-muted-foreground">{venue.description}</p>}
        </div>

        <ul className="flex flex-col gap-1.5 text-sm text-muted-foreground">
          {place && (
            <li className="flex items-start gap-2">
              <MapPin className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
              <span className="line-clamp-1">{place}</span>
            </li>
          )}
          {venue.opening_hours && (
            <li className="flex items-start gap-2">
              <Clock className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
              <span>{venue.opening_hours}</span>
            </li>
          )}
        </ul>

        {venue.facilities.length > 0 && (
          <ul className="flex flex-wrap gap-1.5" aria-label="Facilities">
            {venue.facilities.map((f) => {
              const Icon = FACILITY_ICONS[f]
              const label = FACILITY_LABELS[f] ?? f.replace(/_/g, " ")
              return (
                <li key={f} className="flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-foreground">
                  {Icon && <Icon className="size-3.5 text-accent" aria-hidden />}
                  {label}
                </li>
              )
            })}
          </ul>
        )}

        <div className="mt-auto flex flex-wrap items-center justify-between gap-2 border-t pt-3">
          <div className="flex flex-wrap gap-1.5 text-xs font-semibold">
            {venue.age_range && <span className="rounded-full bg-accent/15 px-2.5 py-1 text-accent">Ages {venue.age_range}</span>}
            {where && <span className="rounded-full bg-muted px-2.5 py-1 text-muted-foreground">{where}</span>}
          </div>
          <div className="flex items-center gap-1">
            {venue.phone && (
              <a
                href={`tel:${venue.phone.replace(/\s+/g, "")}`}
                className="flex size-9 items-center justify-center rounded-full text-foreground transition hover:bg-muted"
              >
                <Phone className="size-4" aria-hidden />
                <span className="sr-only">Call {venue.name}</span>
              </a>
            )}
            {venue.website_url && (
              <a
                href={venue.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-full bg-navy px-3 py-2 text-xs font-bold text-navy-foreground transition hover:opacity-90"
              >
                <Globe className="size-3.5" aria-hidden />
                Website
                <span className="sr-only">for {venue.name}</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}

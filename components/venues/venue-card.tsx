import { VenuePhoto } from "@/components/venues/venue-photo"
import { Accessibility, Baby, Clock, Coffee, Dog, Globe, MapPin, Navigation, Phone, SquareParking, type LucideIcon } from "lucide-react"
import { directionsUrl, formatMiles } from "@/components/venues/venue-spotlight"
import { FACILITY_LABELS, categoryLabel, type Venue } from "@/lib/venue-meta"

const FACILITY_ICONS: Record<string, LucideIcon> = {
  baby_changing: Baby,
  parking: SquareParking,
  cafe: Coffee,
  accessible: Accessibility,
  dog_friendly: Dog,
}

function setting(venue: Venue) {
  if (venue.indoor && venue.outdoor) return "Indoor & outdoor"
  if (venue.indoor) return "Indoor"
  if (venue.outdoor) return "Outdoor"
  return null
}

export function VenueCard({ venue, distance, index = 0 }: { venue: Venue; distance: number | null; index?: number }) {
  const place = [venue.town, venue.postcode].filter(Boolean).join(", ") || venue.address
  const where = setting(venue)

  return (
    <article
      className="group animate-rise flex h-full flex-col overflow-hidden rounded-2xl border bg-card text-card-foreground transition duration-300 hover:-translate-y-1 hover:border-primary/60 hover:shadow-xl hover:shadow-primary/10"
      style={{ animationDelay: `${Math.min(index, 8) * 60}ms` }}
    >
      <div className="relative aspect-[16/10] overflow-hidden">
        <VenuePhoto
          venue={venue}
          sizes="(min-width: 1280px) 30vw, (min-width: 640px) 50vw, 100vw"
          className="object-cover transition duration-500 group-hover:scale-105"
        />
        <span className="absolute top-3 left-3 -rotate-2 rounded-md bg-card px-2.5 py-1 text-xs font-extrabold text-card-foreground shadow-sm transition group-hover:rotate-0">
          {categoryLabel(venue.category)}
        </span>
        {venue.is_free ? (
          <span className="absolute top-3 right-3 rotate-3 rounded-md bg-highlight px-2.5 py-1 text-xs font-extrabold text-highlight-foreground shadow-sm">
            Free!
          </span>
        ) : venue.price_text ? (
          <span className="absolute top-3 right-3 rounded-md bg-navy px-2.5 py-1 text-xs font-bold text-navy-foreground">
            {venue.price_text}
          </span>
        ) : null}
        {distance != null && (
          <span className="absolute top-14 left-3 flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-xs font-extrabold text-primary-foreground">
            <Navigation className="size-3" aria-hidden />
            {formatMiles(distance)}
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="flex flex-col gap-1">
          <h3 className="font-heading text-lg leading-snug font-bold text-pretty">{venue.name}</h3>
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
              <span className="line-clamp-1">{venue.opening_hours}</span>
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
                className="flex size-9 items-center justify-center rounded-full text-foreground transition hover:bg-muted"
              >
                <Globe className="size-4" aria-hidden />
                <span className="sr-only">Website for {venue.name}</span>
              </a>
            )}
            <a
              href={directionsUrl(venue)}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 rounded-full bg-navy px-3 py-2 text-xs font-bold text-navy-foreground transition hover:bg-primary hover:text-primary-foreground dark:bg-muted dark:text-foreground dark:hover:bg-primary dark:hover:text-primary-foreground"
            >
              <Navigation className="size-3.5" aria-hidden />
              Directions
              <span className="sr-only">to {venue.name}</span>
            </a>
          </div>
        </div>
      </div>
    </article>
  )
}

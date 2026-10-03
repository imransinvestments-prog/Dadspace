import { VenuePhoto } from "@/components/venues/venue-photo"
import { Dices, Globe, MapPin, Navigation, X } from "lucide-react"
import { categoryLabel, type Venue } from "@/lib/venue-meta"
import { cn } from "@/lib/utils"

export function directionsUrl(venue: Venue) {
  if (venue.latitude != null && venue.longitude != null) {
    return `https://www.google.com/maps/dir/?api=1&destination=${venue.latitude},${venue.longitude}`
  }
  const q = [venue.name, venue.town, venue.postcode].filter(Boolean).join(", ")
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`
}

export function mapsPlaceUrl(venue: Venue) {
  const q = [venue.name, venue.address ?? venue.town, venue.postcode].filter(Boolean).join(", ")
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`
}

export function formatMiles(miles: number) {
  if (miles < 1) return "Under a mile"
  const rounded = Math.round(miles)
  return `${rounded} ${rounded === 1 ? "mile" : "miles"}`
}

type Props = {
  venue: Venue
  distance: number | null
  rolling: boolean
  onReroll: () => void
  onClose: () => void
}

export function VenueSpotlight({ venue, distance, rolling, onReroll, onClose }: Props) {
  const place = [venue.town, venue.postcode].filter(Boolean).join(", ") || venue.address

  return (
    <section
      aria-label="Surprise pick"
      aria-live={rolling ? "off" : "polite"}
      className="animate-rise relative grid overflow-hidden rounded-2xl border-2 border-primary bg-card text-card-foreground md:grid-cols-[1.1fr_1fr]"
    >
      <div className="relative aspect-[16/10] md:aspect-auto md:min-h-72">
        <VenuePhoto
          venue={venue}
          sizes="(min-width: 768px) 50vw, 100vw"
          className={cn("object-cover transition duration-150", rolling && "scale-105 blur-[2px]")}
        />
        <span className="absolute top-4 left-4 -rotate-3 rounded-md bg-highlight px-3 py-1.5 font-heading text-sm font-extrabold tracking-wide text-highlight-foreground uppercase">
          {rolling ? "Spinning…" : "Today's pick"}
        </span>
      </div>

      <div className="flex flex-col gap-4 p-5 md:p-7">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm font-bold tracking-wide text-primary uppercase">{categoryLabel(venue.category)}</p>
          <button
            type="button"
            onClick={onClose}
            className="-mt-1 -mr-1 flex size-9 items-center justify-center rounded-full text-muted-foreground transition hover:bg-muted hover:text-foreground"
          >
            <X className="size-4" aria-hidden />
            <span className="sr-only">Close surprise pick</span>
          </button>
        </div>

        <h2 className={cn("font-heading text-3xl leading-tight font-extrabold text-balance md:text-4xl", rolling && "opacity-60")}>
          {venue.name}
        </h2>

        <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted-foreground">
          {place && (
            <span className="flex items-center gap-1.5">
              <MapPin className="size-4 text-accent" aria-hidden />
              {place}
            </span>
          )}
          {distance != null && (
            <span className="flex items-center gap-1.5 font-semibold text-foreground">
              <Navigation className="size-4 text-accent" aria-hidden />
              {formatMiles(distance)} away
            </span>
          )}
          {venue.is_free && <span className="font-semibold text-accent">Free entry</span>}
        </div>

        {venue.description && <p className="line-clamp-3 leading-relaxed text-pretty text-muted-foreground">{venue.description}</p>}

        <div className="mt-auto flex flex-wrap gap-2 pt-2">
          <a
            href={directionsUrl(venue)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-extrabold text-primary-foreground transition hover:brightness-105"
          >
            <Navigation className="size-4" aria-hidden />
            {"Let's go"}
          </a>
          {venue.website_url && (
            <a
              href={venue.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-full border bg-card px-4 py-2.5 text-sm font-bold transition hover:bg-muted"
            >
              <Globe className="size-4" aria-hidden />
              Website
            </a>
          )}
          <button
            type="button"
            onClick={onReroll}
            disabled={rolling}
            className="flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-bold text-foreground transition hover:bg-muted disabled:opacity-50"
          >
            <Dices className="size-4" aria-hidden />
            Spin again
          </button>
        </div>
      </div>
    </section>
  )
}

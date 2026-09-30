import { LoaderCircle, LocateFixed, LocateOff } from "lucide-react"
import { EventCard } from "@/components/event-card"
import { EmptyState } from "@/components/empty-state"
import { SectionHeader } from "./section-header"
import type { LocationStatus } from "@/components/location-provider"
import type { HomeData } from "@/lib/types"

type Props = {
  events: HomeData["events"]
  locationStatus: LocationStatus
  sorting: boolean
  onRequestLocation: () => void
}

function titleFor(events: HomeData["events"]) {
  if (events.nearby === "weekend") return "This weekend near you"
  if (events.nearby === "soon") return "Coming up near you"
  if (events.nearby === "nearest") return "Closest to you"
  return events.isWeekend ? "This weekend" : "Coming up soon"
}

function LocationNote({ events, locationStatus, sorting, onRequestLocation }: Props) {
  if (sorting) {
    return (
      <>
        <LoaderCircle className="size-4 shrink-0 animate-spin text-accent" aria-hidden />
        <span>Finding events near you…</span>
      </>
    )
  }
  if (events.nearby) {
    return (
      <>
        <LocateFixed className="size-4 shrink-0 text-accent" aria-hidden />
        <span>
          {events.nearby === "nearest"
            ? `Nothing within ${events.radiusMiles} miles yet, so here are the closest.`
            : `Within ${events.radiusMiles} miles of you, closest first.`}
        </span>
      </>
    )
  }

  const reason =
    locationStatus === "denied"
      ? "Location is blocked for this site, so events aren't sorted by distance. Allow it in your browser settings."
      : locationStatus === "unavailable"
        ? "We couldn't get your location, so events aren't sorted by distance."
        : "Share your location to see events near you."
  return (
    <>
      <LocateOff className="size-4 shrink-0 text-muted-foreground" aria-hidden />
      <span>{reason}</span>
      {locationStatus !== "denied" && (
        <button
          type="button"
          onClick={onRequestLocation}
          className="inline-flex h-9 items-center gap-2 rounded-full border px-3 font-semibold text-foreground transition hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
        >
          <LocateFixed className="size-4" aria-hidden />
          Use my location
        </button>
      )}
    </>
  )
}

export function WeekendEvents(props: Props) {
  const { events } = props
  return (
    <section aria-labelledby="weekend-title" className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <SectionHeader
          id="weekend-title"
          title={titleFor(events)}
          href="/events"
          linkLabel="All events"
          isSample={events.isSample}
        />
        <p role="status" aria-live="polite" className="flex flex-wrap items-center gap-2 text-sm leading-relaxed text-muted-foreground">
          <LocationNote {...props} />
        </p>
      </div>
      {events.items.length ? (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {events.items.map((event, i) => (
            <li key={event.id}>
              <EventCard event={event} index={i} />
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState title="No events here yet." body="Even dads need a nap." />
      )}
    </section>
  )
}

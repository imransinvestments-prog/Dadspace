import { EventCard } from "@/components/event-card"
import { EmptyState } from "@/components/empty-state"
import { SectionHeader } from "./section-header"
import type { HomeData } from "@/lib/types"

export function WeekendEvents({ events }: { events: HomeData["events"] }) {
  return (
    <section aria-labelledby="weekend-title" className="flex flex-col gap-4">
      <SectionHeader
        id="weekend-title"
        title={events.isWeekend ? "This weekend" : "Coming up soon"}
        href="/events"
        linkLabel="All events"
        isSample={events.isSample}
      />
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

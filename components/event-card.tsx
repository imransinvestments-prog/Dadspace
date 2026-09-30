import Image from "next/image"
import { Clock, MapPin, Navigation } from "lucide-react"
import { formatEventDate } from "@/lib/dates"
import type { DadEvent } from "@/lib/types"

function imageFor(event: DadEvent) {
  const text = `${event.title} ${event.description ?? ""}`.toLowerCase()
  if (/swim|football|sport|run|gym|climb|skate|cycle|bike|tennis|leisure/.test(text)) return "/images/event-sport.png"
  if (/story|museum|library|read|book|history|science|exhibit/.test(text)) return "/images/event-story.png"
  if (/craft|art|lego|paint|make|build|draw|messy|music|sing/.test(text)) return "/images/event-crafts.png"
  return "/images/event-outdoor.png"
}

function formatMiles(miles: number) {
  if (miles < 1) return "Under a mile away"
  const rounded = Math.round(miles)
  return `${rounded} ${rounded === 1 ? "mile" : "miles"} away`
}

function isFree(cost: string | null) {
  return !!cost && /\bfree\b/i.test(cost)
}

export function EventCard({ event, index = 0 }: { event: DadEvent; index?: number }) {
  const href = event.event_url || event.source_url
  const free = isFree(event.cost_text)

  const body = (
    <>
      <div className="relative aspect-[16/10] overflow-hidden">
        <Image
          src={imageFor(event) || "/placeholder.svg"}
          alt=""
          fill
          sizes="(min-width: 1024px) 30vw, (min-width: 640px) 50vw, 100vw"
          className="object-cover transition duration-500 group-hover:scale-105"
        />
        <span className="absolute top-3 left-3 rounded-full bg-card px-3 py-1 text-xs font-bold text-card-foreground">
          {formatEventDate(event.start_date, event.end_date)}
        </span>
        {event.cost_text && (
          <span
            className={
              free
                ? "absolute top-3 right-3 rounded-full bg-highlight px-3 py-1 text-xs font-bold text-highlight-foreground"
                : "absolute top-3 right-3 rounded-full bg-navy px-3 py-1 text-xs font-bold text-navy-foreground"
            }
          >
            {free ? "Free" : event.cost_text}
          </span>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-3 p-4">
        <h3 className="font-heading text-lg leading-snug font-bold text-pretty">{event.title}</h3>
        <ul className="flex flex-col gap-1.5 text-sm text-muted-foreground">
          {event.location && (
            <li className="flex items-start gap-2">
              <MapPin className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
              <span className="line-clamp-1">{event.location}</span>
            </li>
          )}
          {event.distance_miles != null && (
            <li className="flex items-start gap-2">
              <Navigation className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
              <span className="font-semibold text-foreground">{formatMiles(event.distance_miles)}</span>
            </li>
          )}
          {event.time_text && (
            <li className="flex items-start gap-2">
              <Clock className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
              <span>{event.time_text}</span>
            </li>
          )}
        </ul>
        {event.age_range && (
          <p className="mt-auto w-fit rounded-full bg-accent/15 px-3 py-1 text-xs font-semibold text-accent">Ages {event.age_range}</p>
        )}
      </div>
    </>
  )

  const className =
    "group animate-rise flex h-full flex-col overflow-hidden rounded-lg border bg-card text-card-foreground transition duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-navy/10"

  return href ? (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className} style={{ animationDelay: `${index * 80}ms` }}>
      {body}
    </a>
  ) : (
    <article className={className} style={{ animationDelay: `${index * 80}ms` }}>
      {body}
    </article>
  )
}

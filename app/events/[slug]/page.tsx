import type { Metadata } from "next"
import Image from "next/image"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeft, CalendarDays, Clock3, ExternalLink, MapPin, Ticket, Users } from "lucide-react"
import { EventCard } from "@/components/event-card"
import { formatEventDate, londonToday } from "@/lib/dates"
import { originalEventDescription } from "@/lib/event-copy"
import { categoryLabel, eventCategory, eventImage, isFreeEvent } from "@/lib/event-meta"
import { eventIdFromSlug, eventSlug } from "@/lib/event-slug"
import { fetchEventById, fetchSimilarUpcomingEvents } from "@/lib/events"
import { pageMetadata, siteUrl } from "@/lib/seo"

type PageProps = { params: Promise<{ slug: string }> }

export const revalidate = 600

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params
  const event = await fetchEventById(eventIdFromSlug(slug))
  if (!event) return pageMetadata("Event not found", "/events", "Browse upcoming family events on Dadspace.", { noIndex: true })
  const canonicalPath = `/events/${eventSlug(event)}`
  return pageMetadata(
    `${event.title} – family event details`,
    canonicalPath,
    originalEventDescription(event),
    { image: eventImage(event).src },
  )
}

export default async function EventDetailPage({ params }: PageProps) {
  const { slug } = await params
  const event = await fetchEventById(eventIdFromSlug(slug))
  if (!event) notFound()

  const today = londonToday()
  const ended = (event.end_date ?? event.start_date).slice(0, 10) < today
  const similar = await fetchSimilarUpcomingEvents(event, 6)
  const image = eventImage(event)
  const category = categoryLabel(eventCategory(event))
  const officialUrl = event.event_url || event.source_url
  const price = event.cost_text ? (isFreeEvent(event.cost_text) ? "Free" : event.cost_text) : "Check price on site"
  const description = originalEventDescription(event)
  const canonical = `${siteUrl}/events/${eventSlug(event)}`

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Event",
    name: event.title,
    description,
    startDate: event.start_date,
    endDate: event.end_date || event.start_date,
    url: canonical,
    eventStatus: ended ? undefined : "https://schema.org/EventScheduled",
    image: image.src.startsWith("http") ? image.src : `${siteUrl}${image.src}`,
    location: event.location
      ? { "@type": "Place", name: event.location, address: event.location }
      : undefined,
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />

      <Link href="/events" className="inline-flex w-fit items-center gap-2 text-sm font-bold text-primary hover:underline">
        <ArrowLeft className="size-4" aria-hidden />
        Back to all events
      </Link>

      {ended && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 px-5 py-4 text-amber-950 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-100">
          <p className="font-heading text-lg font-extrabold">This event has ended</p>
          <p className="mt-1 text-sm">We keep this page available for reference. Current family events are shown below.</p>
        </div>
      )}

      <article className="overflow-hidden rounded-2xl border bg-card">
        <div className="grid lg:grid-cols-2">
          <div className="relative min-h-[300px] bg-muted lg:min-h-[520px]">
            <Image
              src={image.src || "/placeholder.svg"}
              alt={image.isOwn ? event.title : ""}
              fill
              priority
              unoptimized={image.isOwn}
              sizes="(min-width: 1024px) 50vw, 100vw"
              className="object-cover"
            />
          </div>

          <div className="flex flex-col gap-6 p-6 md:p-9">
            <div className="flex flex-col gap-3">
              <p className="text-sm font-bold tracking-wide text-primary uppercase">{category}</p>
              <h1 className="font-heading text-3xl font-extrabold tracking-tight text-balance md:text-4xl">{event.title}</h1>
              <p className="leading-relaxed text-muted-foreground">{description}</p>
            </div>

            <dl className="grid gap-4 sm:grid-cols-2">
              <div className="flex gap-3 rounded-xl bg-muted/60 p-4">
                <CalendarDays className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
                <div><dt className="text-xs font-bold uppercase text-muted-foreground">Date</dt><dd className="mt-1 font-semibold">{formatEventDate(event.start_date, event.end_date)}</dd></div>
              </div>
              <div className="flex gap-3 rounded-xl bg-muted/60 p-4">
                <Clock3 className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
                <div><dt className="text-xs font-bold uppercase text-muted-foreground">Time</dt><dd className="mt-1 font-semibold">{event.time_text || "Check time on site"}</dd></div>
              </div>
              <div className="flex gap-3 rounded-xl bg-muted/60 p-4">
                <Ticket className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
                <div><dt className="text-xs font-bold uppercase text-muted-foreground">Price</dt><dd className="mt-1 font-semibold">{price}</dd></div>
              </div>
              <div className="flex gap-3 rounded-xl bg-muted/60 p-4">
                <Users className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
                <div><dt className="text-xs font-bold uppercase text-muted-foreground">Ages</dt><dd className="mt-1 font-semibold">{event.age_range || "Check age guidance"}</dd></div>
              </div>
            </dl>

            {event.location && (
              <div className="flex gap-3 rounded-xl border p-4">
                <MapPin className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
                <div><p className="text-xs font-bold uppercase text-muted-foreground">Where</p><p className="mt-1 font-semibold">{event.location}</p></div>
              </div>
            )}

            {officialUrl && (
              <a
                href={officialUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-navy px-6 py-3.5 text-sm font-bold text-navy-foreground transition hover:-translate-y-0.5 hover:shadow-lg sm:w-fit"
              >
                {ended ? "View organiser's page" : "Book / check official site"}
                <ExternalLink className="size-4" aria-hidden />
              </a>
            )}

            <p className="text-xs leading-relaxed text-muted-foreground">
              Dadspace writes its own short summary from the structured event facts. Times, prices and availability can change, so check the official listing before travelling.
            </p>
          </div>
        </div>
      </article>

      {similar.length > 0 && (
        <section className="flex flex-col gap-5" aria-labelledby="similar-events">
          <div>
            <p className="text-sm font-bold tracking-wide text-primary uppercase">Keep planning</p>
            <h2 id="similar-events" className="font-heading text-2xl font-extrabold md:text-3xl">
              {ended ? "Similar upcoming events" : "You might also like"}
            </h2>
          </div>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {similar.map((item, index) => (
              <li key={item.id}><EventCard event={item} index={index} showCategory /></li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

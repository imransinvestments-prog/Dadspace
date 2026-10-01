import Image from "next/image"
import { EventsExplorer } from "@/components/events/events-explorer"
import { EventsJsonLd } from "@/components/events/events-json-ld"
import { EventsFaq } from "@/components/events/events-faq"
import { fetchUpcomingEvents } from "@/lib/events"
import { isFreeEvent } from "@/lib/event-meta"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Family Events & Things to Do With Kids This Weekend",
  "/events",
  "Upcoming family events across the UK: free kids' activities, weekend days out, story times, sport, swimming, crafts and seasonal events for dads and children.",
  { image: "/images/events/family-day.png" },
)

export const revalidate = 600

export default async function EventsPage() {
  const { events, today, saturday, sunday, isSample } = await fetchUpcomingEvents()
  const weekendCount = events.filter(
    (e) => e.start_date.slice(0, 10) <= sunday && (e.end_date ?? e.start_date).slice(0, 10) >= saturday,
  ).length
  const freeCount = events.filter((e) => isFreeEvent(e.cost_text)).length

  return (
    <div className="flex flex-col gap-10">
      <EventsJsonLd events={events} />

      <header className="grid items-center gap-6 overflow-hidden rounded-2xl bg-navy text-navy-foreground md:grid-cols-5">
        <div className="flex flex-col gap-4 p-6 md:col-span-3 md:p-10">
          <p className="text-sm font-bold tracking-wide text-highlight uppercase">What&apos;s on</p>
          <h1 className="font-heading text-4xl font-extrabold tracking-tight text-balance md:text-5xl">
            Family events and things to do with the kids
          </h1>
          <p className="max-w-xl leading-relaxed text-pretty opacity-85">
            Story times, swimming, sport, crafts and days out from councils, libraries and venues across the UK. Refreshed regularly, so the weekend plan is easier to sort before the kids are.
          </p>
          <dl className="flex flex-wrap gap-x-8 gap-y-2 pt-2">
            <div className="flex items-baseline gap-2">
              <dt className="order-2 text-sm opacity-80">on this weekend</dt>
              <dd className="font-heading text-3xl font-extrabold text-highlight">{weekendCount}</dd>
            </div>
            <div className="flex items-baseline gap-2">
              <dt className="order-2 text-sm opacity-80">free to go to</dt>
              <dd className="font-heading text-3xl font-extrabold">{freeCount}</dd>
            </div>
          </dl>
          {isSample && <p className="text-sm opacity-70">Showing example events while the live listings load.</p>}
        </div>
        <div className="relative hidden aspect-[4/5] h-full md:col-span-2 md:block">
          <Image
            src="/images/events/family-day.png"
            alt="A dad carrying his daughter on his shoulders at a busy family fun day"
            fill
            priority
            sizes="40vw"
            className="object-cover"
          />
        </div>
      </header>

      <EventsExplorer events={events} today={today} saturday={saturday} sunday={sunday} />

      <EventsFaq />
    </div>
  )
}

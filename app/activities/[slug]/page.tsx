import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeft, CalendarClock, ExternalLink, MapPin, Ticket, Users } from "lucide-react"
import { originalActivityDescription } from "@/lib/activity-copy"
import { activityIdFromSlug, activitySlug } from "@/lib/activity-slug"
import { fetchActivityById, fetchSimilarActivities } from "@/lib/activities"
import { pageMetadata, siteUrl } from "@/lib/seo"

type PageProps = { params: Promise<{ slug: string }> }

export const revalidate = 600

function label(value: string | null | undefined) {
  if (!value) return "Family activity"
  return value.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase())
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params
  const activity = await fetchActivityById(activityIdFromSlug(slug))
  if (!activity) {
    return pageMetadata("Activity not found", "/activities", "Browse regular family activities on Dadspace.", { noIndex: true })
  }
  return pageMetadata(
    `${activity.title} – family activity details`,
    `/activities/${activitySlug(activity)}`,
    originalActivityDescription(activity),
  )
}

export default async function ActivityDetailPage({ params }: PageProps) {
  const { slug } = await params
  const activity = await fetchActivityById(activityIdFromSlug(slug))
  if (!activity) notFound()

  const similar = await fetchSimilarActivities(activity, 6)
  const canonical = `${siteUrl}/activities/${activitySlug(activity)}`
  const description = originalActivityDescription(activity)
  const placeName = activity.venue_name || activity.location
  const officialUrl = activity.event_url || activity.source_url
  const price = activity.cost_text || "Check price on site"

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebPage",
        "@id": canonical,
        url: canonical,
        name: `${activity.title} – family activity details`,
        description,
        mainEntity: { "@id": `${canonical}#activity` },
      },
      {
        "@type": "Thing",
        "@id": `${canonical}#activity`,
        name: activity.title,
        description,
        category: label(activity.category),
        url: canonical,
        location: placeName
          ? {
              "@type": "Place",
              name: placeName,
              address: activity.venue_address || activity.postcode || activity.location || undefined,
            }
          : undefined,
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "Activities", item: `${siteUrl}/activities` },
          { "@type": "ListItem", position: 2, name: activity.title, item: canonical },
        ],
      },
    ],
  }

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />

      <Link href="/activities" className="inline-flex w-fit items-center gap-2 text-sm font-bold text-primary hover:underline">
        <ArrowLeft className="size-4" aria-hidden />
        Back to all activities
      </Link>

      <article className="rounded-2xl border bg-card p-6 md:p-9">
        <div className="flex flex-col gap-6">
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-primary">{label(activity.category)}</p>
            <h1 className="mt-2 font-heading text-3xl font-extrabold tracking-tight md:text-4xl">{activity.title}</h1>
            <p className="mt-4 max-w-3xl leading-relaxed text-muted-foreground">{description}</p>
          </div>

          <dl className="grid gap-4 sm:grid-cols-2">
            <div className="flex gap-3 rounded-xl bg-muted/60 p-4">
              <CalendarClock className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
              <div><dt className="text-xs font-bold uppercase text-muted-foreground">Schedule</dt><dd className="mt-1 font-semibold">{activity.schedule_text || activity.time_text || "Check schedule on site"}</dd></div>
            </div>
            <div className="flex gap-3 rounded-xl bg-muted/60 p-4">
              <Ticket className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
              <div><dt className="text-xs font-bold uppercase text-muted-foreground">Price</dt><dd className="mt-1 font-semibold">{price}</dd></div>
            </div>
            <div className="flex gap-3 rounded-xl bg-muted/60 p-4">
              <Users className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
              <div><dt className="text-xs font-bold uppercase text-muted-foreground">Ages</dt><dd className="mt-1 font-semibold">{activity.age_range || "Check age guidance"}</dd></div>
            </div>
            <div className="flex gap-3 rounded-xl bg-muted/60 p-4">
              <MapPin className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
              <div>
                <dt className="text-xs font-bold uppercase text-muted-foreground">Where</dt>
                <dd className="mt-1 font-semibold">
                  {[placeName, activity.venue_address, activity.postcode].filter(Boolean).filter((value, index, all) => all.indexOf(value) === index).join(", ") || "Check venue on site"}
                </dd>
              </div>
            </div>
          </dl>

          {officialUrl && (
            <a
              href={officialUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-navy px-6 py-3.5 text-sm font-bold text-navy-foreground transition hover:-translate-y-0.5 hover:shadow-lg sm:w-fit"
            >
              Check official site <ExternalLink className="size-4" aria-hidden />
            </a>
          )}

          <p className="text-xs leading-relaxed text-muted-foreground">
            Dadspace writes its own summary from structured listing facts. Schedules, prices and availability can change, so check the organiser&apos;s page before travelling.
          </p>
        </div>
      </article>

      {similar.length > 0 && (
        <section className="flex flex-col gap-5" aria-labelledby="similar-activities">
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-primary">More regular activities</p>
            <h2 id="similar-activities" className="font-heading text-2xl font-extrabold md:text-3xl">You might also like</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {similar.map((item) => (
              <article key={item.id} className="rounded-2xl border bg-card p-5">
                <p className="text-xs font-bold uppercase tracking-wide text-highlight">{label(item.category)}</p>
                <h3 className="mt-1 font-heading text-lg font-extrabold">
                  <Link href={`/activities/${activitySlug(item)}`} className="hover:underline">{item.title}</Link>
                </h3>
                {item.schedule_text && <p className="mt-2 text-sm">{item.schedule_text}</p>}
                <Link href={`/activities/${activitySlug(item)}`} className="mt-3 inline-block text-sm font-semibold underline underline-offset-4">View details</Link>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

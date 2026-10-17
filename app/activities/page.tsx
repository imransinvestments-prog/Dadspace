import { ActivitiesExplorer } from "@/components/activities/activities-explorer"
import { ACTIVITY_PAGE_SIZE, fetchActivityCategories, fetchActivityPage } from "@/lib/activities"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Kids' Activities, Classes & Clubs",
  "/activities",
  "Regular family activities across the UK: weekly classes, clubs, toddler groups, swimming, sport and term-time sessions for children and parents.",
  {image:"/images/event-outdoor.png"},
)

export const revalidate = 600

export default async function ActivitiesPage() {
  const [initialPage, categories] = await Promise.all([
    fetchActivityPage({ limit: ACTIVITY_PAGE_SIZE }),
    fetchActivityCategories(),
  ])
  if (initialPage.loadFailed) return <section className="rounded-2xl border bg-card p-8"><h1 className="text-3xl font-bold">Activities are temporarily unavailable</h1><p role="status" className="mt-3 text-muted-foreground">We could not load the listings. Please try again shortly.</p><a href="/activities" className="mt-5 inline-block font-semibold underline">Try again</a></section>

  return (
    <div className="flex flex-col gap-3 md:gap-10">
      <header className="rounded-2xl bg-navy p-3 text-navy-foreground md:p-10">
        <p className="hidden text-sm font-bold uppercase tracking-wide text-highlight md:block">Regular things to join</p>
        <h1 className="mt-2 font-heading text-2xl font-extrabold tracking-tight md:text-5xl">Activities, classes and clubs</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed opacity-85 md:mt-4 md:text-base">
          Weekly and term-time groups, classes and clubs. Check the organiser for current schedules.
        </p>
      </header>

      <ActivitiesExplorer initialPage={initialPage} categories={categories} />
    </div>
  )
}

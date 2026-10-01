import { ActivitiesExplorer } from "@/components/activities/activities-explorer"
import { fetchCurrentActivities } from "@/lib/activities"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Kids' Activities, Classes & Clubs",
  "/activities",
  "Regular family activities across the UK: weekly classes, clubs, toddler groups, swimming, sport and term-time sessions for children and parents.",
)

export const revalidate = 600

export default async function ActivitiesPage() {
  const activities = await fetchCurrentActivities()

  return (
    <div className="flex flex-col gap-10">
      <header className="rounded-2xl bg-navy p-6 text-navy-foreground md:p-10">
        <p className="text-sm font-bold uppercase tracking-wide text-highlight">Regular things to join</p>
        <h1 className="mt-3 font-heading text-4xl font-extrabold tracking-tight md:text-5xl">Activities, classes and clubs</h1>
        <p className="mt-4 max-w-2xl leading-relaxed opacity-85">
          Weekly and term-time activities for families: sport, swimming, toddler groups, arts, clubs and classes. Schedules come from the organiser&apos;s page and listings disappear if we stop seeing them for 60 days.
        </p>
      </header>

      <ActivitiesExplorer activities={activities} />
    </div>
  )
}

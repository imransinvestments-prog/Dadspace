import Link from 'next/link'
import { MapPin } from 'lucide-react'
import { activitySlug } from '@/lib/activity-slug'
import { activityPrice, activitySource } from '@/lib/activity-presentation'
import type { DadActivity } from '@/lib/types'
import { ActivityScheduleSummary } from './activity-schedule'

export function ActivityCard({activity, showDistance = false}: {activity: DadActivity; showDistance?: boolean}) {
  const source = activitySource(activity)
  const place = [activity.venue_name || activity.location, activity.postcode].filter(Boolean).join(', ')
  return <article className="flex min-w-0 flex-col gap-4 rounded-2xl border bg-card p-5 shadow-sm [overflow-wrap:anywhere]">
    <div>
      <p className="text-xs font-bold uppercase tracking-wide text-highlight">{activity.category?.replace(/_/g,' ') || 'Other'}</p>
      <h2 className="font-heading text-xl font-extrabold leading-tight"><Link href={`/activities/${activitySlug(activity)}`} className="hover:underline">{activity.title}</Link></h2>
    </div>
    <dl className="space-y-3 text-sm">
      <div><dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Schedule</dt><dd className="mt-1"><ActivityScheduleSummary activity={activity} compact /></dd></div>
      <div><dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Age guidance</dt><dd className="mt-1">{activity.age_range?.trim() || 'Age guidance not supplied'}</dd></div>
      <div><dt className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Price</dt><dd className="mt-1 font-semibold">{activityPrice(activity.cost_text)}</dd></div>
    </dl>
    {place && <p className="flex gap-2 text-sm text-muted-foreground"><MapPin className="mt-0.5 size-4 shrink-0" aria-hidden /><span>{place}</span></p>}
    {showDistance && <p className="text-sm font-semibold">{activity.distance_miles == null ? 'Distance unavailable' : `About ${activity.distance_miles < 1 ? 'less than 1' : Math.round(activity.distance_miles)} miles away (straight-line)`}</p>}
    {activity.description && <p className="line-clamp-3 text-sm leading-relaxed text-muted-foreground">{activity.description}</p>}
    <div className="mt-auto flex flex-wrap gap-x-5 gap-y-3 border-t pt-3 text-sm font-semibold">
      <Link href={`/activities/${activitySlug(activity)}`} className="underline underline-offset-4">View activity details<span className="sr-only"> for {activity.title}</span></Link>
      {source && <a href={source} target="_blank" rel="noopener noreferrer" className="underline underline-offset-4">Check source<span className="sr-only"> for {activity.title} (opens a new tab)</span></a>}
    </div>
  </article>
}

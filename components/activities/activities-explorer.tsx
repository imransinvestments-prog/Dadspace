"use client"

import Link from "next/link"
import { useState } from "react"
import { useLocation } from "@/components/location-provider"
import { LocationControls } from "@/components/location-controls"
import { useDirectoryPage } from "@/hooks/use-directory-page"
import { MapPin, Search } from "lucide-react"
import { activitySlug } from "@/lib/activity-slug"
import { ACTIVITY_PAGE_SIZE, type ActivityPage } from "@/lib/activity-shared"
import type { DadActivity } from "@/lib/types"

function priceLabel(value: string | null) {
  return value?.trim() || "Check price on site"
}

function categoryLabel(value: string | null | undefined) {
  if (!value) return "Other"
  return value.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase())
}

export function ActivitiesExplorer({ initialPage, categories }: { initialPage: ActivityPage; categories: string[] }) {
  const {coords,browseAll}=useLocation()
  const [query,setQuery]=useState("")
  const [category,setCategory]=useState("all")
  const params=new URLSearchParams({q:query,category,limit:String(ACTIVITY_PAGE_SIZE)})
  if(coords){params.set('lat',String(coords.lat));params.set('lng',String(coords.lng))}
  const enabled=Boolean(coords)||browseAll
  const feed=useDirectoryPage<ActivityPage>('/api/activities?'+params,enabled)
  const activities=feed.pages.flatMap(p=>p.activities)
  const total=feed.pages.at(-1)?.total??0
  const hasMore=feed.pages.at(-1)?.hasMore??false
  const {loading,error}=feed
  const loadMore=()=>feed.loadMore(activities.length)
  return (
    <section className="flex flex-col gap-6">
      <LocationControls />
      <div className="grid gap-3 rounded-2xl border bg-card p-4 md:grid-cols-[1fr_220px]">
        <label className="relative">
          <span className="sr-only">Search activities</span>
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 opacity-60" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search classes, clubs, venues or ages"
            className="w-full rounded-xl border bg-background py-2.5 pl-9 pr-3"
          />
        </label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-xl border bg-background px-3 py-2.5"
          aria-label="Activity category"
        >
          <option value="all">All activity types</option>
          {categories.map((value) => (
            <option key={value} value={value}>{categoryLabel(value)}</option>
          ))}
        </select>
      </div>

      <p className="text-sm opacity-70" aria-live="polite">
        {loading && !activities.length ? "Loading activitiesâ€¦" : enabled ? `${total} current ${total === 1 ? "activity" : "activities"}${coords ? ", nearest first" : ""}` : "Choose a location or browse all UK to see activities."}
      </p>
      {error && <p role="alert">{error} <button onClick={feed.retry} className="underline">Retry</button></p>}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {activities.map((activity) => (
          <article key={activity.id} className="flex flex-col gap-3 rounded-2xl border bg-card p-5 shadow-sm">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-highlight">{categoryLabel(activity.category)}</p>
              <h2 className="font-heading text-xl font-extrabold leading-tight">
                <Link href={`/activities/${activitySlug(activity)}`} className="hover:underline">
                  {activity.title}
                </Link>
              </h2>
            </div>

            {activity.schedule_text && <p className="font-semibold">{activity.schedule_text}</p>}
            {activity.age_range && <p className="text-sm">Ages: {activity.age_range}</p>}
            <p className="text-sm font-semibold">{priceLabel(activity.cost_text)}</p>

            {(activity.venue_name || activity.location || activity.postcode) && (
              <p className="flex gap-2 text-sm opacity-80">
                <MapPin className="mt-0.5 size-4 shrink-0" />
                <span>{[activity.venue_name || activity.location, activity.postcode].filter(Boolean).join(", ")}</span>
              </p>
            )}

            {coords && <p className="text-sm font-semibold">{activity.distance_miles == null ? 'Distance unavailable' : `About ${activity.distance_miles < 1 ? 'less than 1' : Math.round(activity.distance_miles)} miles away`}</p>}
            {activity.description && <p className="line-clamp-3 text-sm leading-relaxed opacity-80">{activity.description}</p>}

            <Link
              href={`/activities/${activitySlug(activity)}`}
              className="mt-auto inline-flex items-center font-semibold underline underline-offset-4"
            >
              View activity details
            </Link>
          </article>
        ))}
      </div>

      {hasMore && (
        <button
          type="button"
          onClick={loadMore}
          disabled={loading}
          className="mx-auto rounded-xl border px-5 py-2.5 font-semibold disabled:opacity-60"
        >
          {loading ? "Loadingâ€¦" : "Load more"}
        </button>
      )}

      {enabled && !loading && !error && !activities.length && <p className="rounded-2xl border bg-card p-6 text-center">No activities match those filters yet.</p>}
    </section>
  )
}

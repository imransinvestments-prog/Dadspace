"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"
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

async function fetchPage({ offset, query, category, signal }: {
  offset: number
  query: string
  category: string
  signal?: AbortSignal
}): Promise<ActivityPage> {
  const params = new URLSearchParams({ offset: String(offset), limit: String(ACTIVITY_PAGE_SIZE) })
  if (query.trim()) params.set("q", query.trim())
  if (category !== "all") params.set("category", category)
  const response = await fetch(`/api/activities?${params.toString()}`, { signal })
  if (!response.ok) throw new Error("Could not load activities")
  return response.json() as Promise<ActivityPage>
}

export function ActivitiesExplorer({ initialPage, categories }: { initialPage: ActivityPage; categories: string[] }) {
  const [query, setQuery] = useState("")
  const [category, setCategory] = useState("all")
  const [activities, setActivities] = useState<DadActivity[]>(initialPage.activities)
  const [total, setTotal] = useState(initialPage.total)
  const [hasMore, setHasMore] = useState(initialPage.hasMore)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const firstRun = useRef(true)

  useEffect(() => {
    if (firstRun.current) {
      firstRun.current = false
      return
    }
    const controller = new AbortController()
    const timer = window.setTimeout(async () => {
      setLoading(true)
      setError("")
      try {
        const page = await fetchPage({ offset: 0, query, category, signal: controller.signal })
        setActivities(page.activities)
        setTotal(page.total)
        setHasMore(page.hasMore)
      } catch (err) {
        if ((err as Error).name !== "AbortError") setError("Activities could not be refreshed. Please try again.")
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }, 250)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [query, category])

  async function loadMore() {
    setLoading(true)
    setError("")
    try {
      const page = await fetchPage({ offset: activities.length, query, category })
      setActivities((current) => {
        const seen = new Set(current.map((item) => item.id))
        return [...current, ...page.activities.filter((item) => !seen.has(item.id))]
      })
      setTotal(page.total)
      setHasMore(page.hasMore)
    } catch {
      setError("More activities could not be loaded. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="flex flex-col gap-6">
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
        {loading && !activities.length ? "Loading activities…" : `${total} current ${total === 1 ? "activity" : "activities"}`}
      </p>
      {error && <p className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-950">{error}</p>}

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
          {loading ? "Loading…" : "Load more"}
        </button>
      )}

      {!loading && !activities.length && <p className="rounded-2xl border bg-card p-6 text-center">No activities match those filters yet.</p>}
    </section>
  )
}

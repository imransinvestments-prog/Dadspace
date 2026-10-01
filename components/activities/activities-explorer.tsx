"use client"

import { useMemo, useState } from "react"
import { ExternalLink, MapPin, Search } from "lucide-react"
import type { DadActivity } from "@/lib/types"

const PAGE_SIZE = 24

function priceLabel(value: string | null) {
  return value?.trim() || "Check price on site"
}

function categoryLabel(value: string | null | undefined) {
  if (!value) return "Other"
  return value.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase())
}

export function ActivitiesExplorer({ activities }: { activities: DadActivity[] }) {
  const [query, setQuery] = useState("")
  const [category, setCategory] = useState("all")
  const [visible, setVisible] = useState(PAGE_SIZE)

  const categories = useMemo(
    () => [...new Set(activities.map((a) => a.category).filter((v): v is string => !!v))].sort(),
    [activities],
  )

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return activities.filter((activity) => {
      if (category !== "all" && activity.category !== category) return false
      if (!q) return true
      const haystack = [
        activity.title,
        activity.description,
        activity.schedule_text,
        activity.location,
        activity.venue_name,
        activity.postcode,
        activity.age_range,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [activities, category, query])

  const shown = filtered.slice(0, visible)

  return (
    <section className="flex flex-col gap-6">
      <div className="grid gap-3 rounded-2xl border bg-card p-4 md:grid-cols-[1fr_220px]">
        <label className="relative">
          <span className="sr-only">Search activities</span>
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 opacity-60" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setVisible(PAGE_SIZE)
            }}
            placeholder="Search classes, clubs, venues or ages"
            className="w-full rounded-xl border bg-background py-2.5 pl-9 pr-3"
          />
        </label>
        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value)
            setVisible(PAGE_SIZE)
          }}
          className="rounded-xl border bg-background px-3 py-2.5"
          aria-label="Activity category"
        >
          <option value="all">All activity types</option>
          {categories.map((value) => (
            <option key={value} value={value}>{categoryLabel(value)}</option>
          ))}
        </select>
      </div>

      <p className="text-sm opacity-70">{filtered.length} current {filtered.length === 1 ? "activity" : "activities"}</p>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {shown.map((activity) => (
          <article key={activity.id} className="flex flex-col gap-3 rounded-2xl border bg-card p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-wide text-highlight">{categoryLabel(activity.category)}</p>
                <h2 className="font-heading text-xl font-extrabold leading-tight">{activity.title}</h2>
              </div>
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

            {activity.event_url && (
              <a
                href={activity.event_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-auto inline-flex items-center gap-2 font-semibold underline underline-offset-4"
              >
                Check official site <ExternalLink className="size-4" />
              </a>
            )}
          </article>
        ))}
      </div>

      {shown.length < filtered.length && (
        <button
          type="button"
          onClick={() => setVisible((count) => count + PAGE_SIZE)}
          className="mx-auto rounded-xl border px-5 py-2.5 font-semibold"
        >
          Load more
        </button>
      )}

      {!filtered.length && <p className="rounded-2xl border bg-card p-6 text-center">No activities match those filters yet.</p>}
    </section>
  )
}

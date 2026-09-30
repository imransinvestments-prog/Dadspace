"use client"

import { useMemo, useState } from "react"
import { Info, LocateFixed, Search, X } from "lucide-react"
import { useLocation } from "@/components/location-provider"
import { VenueCard } from "@/components/venues/venue-card"
import { categoryLabel, milesBetween, type Venue } from "@/lib/venue-meta"
import { cn } from "@/lib/utils"

type Toggle = "free" | "indoor" | "outdoor"

const TOGGLES: { key: Toggle; label: string }[] = [
  { key: "free", label: "Free entry" },
  { key: "indoor", label: "Indoor" },
  { key: "outdoor", label: "Outdoor" },
]

const chip = (active: boolean) =>
  cn(
    "shrink-0 rounded-full border px-3.5 py-1.5 text-sm font-semibold transition",
    active ? "border-navy bg-navy text-navy-foreground dark:border-primary dark:bg-primary dark:text-primary-foreground" : "bg-card text-foreground hover:bg-muted",
  )

export function VenuesDirectory({ venues, isPreview }: { venues: Venue[]; isPreview: boolean }) {
  const { coords, status, request } = useLocation()
  const [query, setQuery] = useState("")
  const [category, setCategory] = useState("all")
  const [toggles, setToggles] = useState<Set<Toggle>>(new Set())

  const categories = useMemo(
    () => Array.from(new Set(venues.map((v) => v.category).filter((c): c is string => !!c))).sort(),
    [venues],
  )

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    return venues
      .filter((v) => category === "all" || v.category === category)
      .filter((v) => !toggles.has("free") || v.is_free)
      .filter((v) => !toggles.has("indoor") || v.indoor)
      .filter((v) => !toggles.has("outdoor") || v.outdoor)
      .filter((v) => !q || [v.name, v.town, v.postcode, v.description].some((s) => s?.toLowerCase().includes(q)))
      .map((v) => ({
        venue: v,
        distance:
          coords && v.latitude != null && v.longitude != null ? milesBetween(coords, { lat: v.latitude, lng: v.longitude }) : null,
      }))
      .sort((a, b) => {
        if (a.distance != null && b.distance != null) return a.distance - b.distance
        if (a.distance != null) return -1
        if (b.distance != null) return 1
        return a.venue.name.localeCompare(b.venue.name)
      })
  }, [venues, query, category, toggles, coords])

  const toggle = (key: Toggle) =>
    setToggles((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })

  const filtered = query !== "" || category !== "all" || toggles.size > 0
  const clear = () => {
    setQuery("")
    setCategory("all")
    setToggles(new Set())
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 md:px-8 md:py-10">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="font-heading text-3xl font-extrabold text-balance md:text-4xl">Venues</h1>
          <p className="max-w-xl leading-relaxed text-pretty text-muted-foreground">
            Soft play, parks, museums and more — places worth the car journey, with the facilities you actually need to know about.
          </p>
        </div>
        <LocationStatus status={status} onRetry={request} />
      </header>

      {isPreview && (
        <div role="note" className="flex items-start gap-3 rounded-lg border border-dashed bg-card p-4 text-sm leading-relaxed">
          <Info className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden />
          <p>
            <span className="font-bold">Preview layout.</span>{" "}
            <span className="text-muted-foreground">
              These are sample venues. The page will switch to your <code className="font-mono">venues</code> table automatically once it has
              data.
            </span>
          </p>
        </div>
      )}

      <div className="flex flex-col gap-3">
        <label className="relative block">
          <span className="sr-only">Search venues</span>
          <Search className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, town or postcode"
            className="h-12 w-full rounded-full border bg-card pr-4 pl-11 text-base text-foreground placeholder:text-muted-foreground focus-visible:outline-2 focus-visible:outline-ring"
          />
        </label>

        <div className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 md:mx-0 md:flex-wrap md:px-0" role="group" aria-label="Venue type">
          <button type="button" className={chip(category === "all")} aria-pressed={category === "all"} onClick={() => setCategory("all")}>
            All types
          </button>
          {categories.map((c) => (
            <button key={c} type="button" className={chip(category === c)} aria-pressed={category === c} onClick={() => setCategory(c)}>
              {categoryLabel(c)}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filters">
          {TOGGLES.map((t) => (
            <button
              key={t.key}
              type="button"
              aria-pressed={toggles.has(t.key)}
              onClick={() => toggle(t.key)}
              className={cn(
                "rounded-full px-3 py-1 text-xs font-bold transition",
                toggles.has(t.key) ? "bg-accent text-accent-foreground" : "bg-muted text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
            </button>
          ))}
          {filtered && (
            <button
              type="button"
              onClick={clear}
              className="flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold text-muted-foreground hover:text-foreground"
            >
              <X className="size-3.5" aria-hidden />
              Clear
            </button>
          )}
        </div>
      </div>

      <p className="text-sm font-semibold text-muted-foreground" aria-live="polite">
        {results.length} {results.length === 1 ? "venue" : "venues"}
        {coords ? ", nearest first" : ""}
      </p>

      {results.length > 0 ? (
        <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {results.map(({ venue, distance }, i) => (
            <li key={venue.id}>
              <VenueCard venue={venue} distance={distance} index={i} />
            </li>
          ))}
        </ul>
      ) : (
        <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed bg-card px-6 py-12 text-center">
          <p className="font-heading text-lg font-bold">No venues match those filters</p>
          <p className="text-sm text-muted-foreground">Try a different type or clear the filters.</p>
          <button type="button" onClick={clear} className="rounded-full bg-primary px-4 py-2 text-sm font-bold text-primary-foreground">
            Clear filters
          </button>
        </div>
      )}
    </div>
  )
}

function LocationStatus({ status, onRetry }: { status: string; onRetry: () => void }) {
  if (status === "ready") {
    return (
      <p className="flex items-center gap-2 text-sm font-semibold text-accent">
        <LocateFixed className="size-4" aria-hidden />
        Sorted by distance from you
      </p>
    )
  }
  if (status === "locating") {
    return <p className="text-sm text-muted-foreground">Finding your location…</p>
  }
  return (
    <button
      type="button"
      onClick={onRetry}
      className="flex w-fit items-center gap-2 rounded-full border bg-card px-4 py-2 text-sm font-semibold transition hover:bg-muted"
    >
      <LocateFixed className="size-4 text-accent" aria-hidden />
      Use my location
    </button>
  )
}

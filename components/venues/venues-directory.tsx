"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Dices, Info, Search, X } from "lucide-react"
import { useLocation } from "@/components/location-provider"
import { LocationControls } from "@/components/location-controls"
import { useDirectoryPage } from "@/hooks/use-directory-page"
import { CategoryRail } from "@/components/venues/category-rail"
import { VenueCard } from "@/components/venues/venue-card"
import { VenueSpotlight } from "@/components/venues/venue-spotlight"
import { categoryPlural, milesBetween, type Venue } from "@/lib/venue-meta"
import { cn } from "@/lib/utils"

type Toggle = "free" | "indoor" | "outdoor"

const TOGGLES: { key: Toggle; label: string }[] = [
  { key: "free", label: "Free entry" },
  { key: "indoor", label: "Rainy-day proof" },
  { key: "outdoor", label: "Outdoors" },
]

const SPIN_STEPS = 14
const SPIN_INTERVAL_MS = 70

type Result = { venue: Venue; distance: number | null }

export function VenuesDirectory({ venues, isPreview, allCategories = [] }: { venues: Venue[]; isPreview: boolean; allCategories?: {key:string;count:number}[] }) {
  const { coords, browseAll } = useLocation()
  const [query, setQuery] = useState("")
  const [category, setCategory] = useState("all")
  const [toggles, setToggles] = useState<Set<Toggle>>(new Set())
  const [pick, setPick] = useState<Result | null>(null)
  const [rolling, setRolling] = useState(false)
  const spinTimer = useRef<number | null>(null)
  const spotlightRef = useRef<HTMLDivElement>(null)

  const enabled=Boolean(coords)||browseAll
  const params=new URLSearchParams({q:query,category,free:String(toggles.has('free')),indoor:String(toggles.has('indoor')),outdoor:String(toggles.has('outdoor'))})
  if(coords){params.set('lat',String(coords.lat));params.set('lng',String(coords.lng))}
  const feed=useDirectoryPage<{venues:Venue[];total:number;hasMore:boolean}>('/api/venues?'+params,enabled&&!isPreview)
  const currentVenues=isPreview?(enabled?venues:[]):feed.pages.flatMap(p=>p.venues)
  const total=isPreview?currentVenues.length:feed.pages.at(-1)?.total??0
  const hasMore=feed.pages.at(-1)?.hasMore??false
  useEffect(()=>{stopSpin();setPick(null);setRolling(false)},[coords,query,category,toggles,browseAll])
  useEffect(() => () => stopSpin(), [])

  const categories = useMemo(() => {
    if(allCategories.length)return allCategories
    const counts = new Map<string, number>()
    for (const v of venues) if (v.category) counts.set(v.category, (counts.get(v.category) ?? 0) + 1)
    return Array.from(counts, ([key, count]) => ({ key, count })).sort((a, b) => b.count - a.count)
  }, [venues,allCategories])

  const results = useMemo<Result[]>(() => {
    const q = query.trim().toLowerCase()
    return currentVenues
      .filter((v) => !isPreview || category === "all" || v.category === category)
      .filter((v) => !isPreview || !toggles.has("free") || v.is_free)
      .filter((v) => !isPreview || !toggles.has("indoor") || v.indoor)
      .filter((v) => !isPreview || !toggles.has("outdoor") || v.outdoor)
      .filter((v) => !isPreview || !q || [v.name, v.town, v.postcode, v.description].some((s) => s?.toLowerCase().includes(q)))
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
  }, [currentVenues, query, category, toggles, coords, isPreview])

  function stopSpin() {
    if (spinTimer.current != null) window.clearInterval(spinTimer.current)
    spinTimer.current = null
  }

  function surprise() {
    // With location on, pick from the nearest 30 so the surprise is actually reachable.
    const pool = coords ? results.slice(0, 30) : results
    if (!pool.length) return
    const random = () => pool[Math.floor(Math.random() * pool.length)]
    const final = random()
    stopSpin()
    requestAnimationFrame(() => spotlightRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }))

    if (pool.length < 2 || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setPick(final)
      return
    }
    setRolling(true)
    let step = 0
    spinTimer.current = window.setInterval(() => {
      step += 1
      if (step >= SPIN_STEPS) {
        stopSpin()
        setPick(final)
        setRolling(false)
      } else {
        setPick(random())
      }
    }, SPIN_INTERVAL_MS)
  }

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

  const heading = category === "all" ? "Everything" : categoryPlural(category)

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 md:px-8 md:py-10">
      <header className="flex flex-col gap-5">
        <p className="w-fit -rotate-2 rounded-md bg-accent px-2.5 py-1 text-xs font-extrabold tracking-widest text-accent-foreground uppercase">
          Days out
        </p>
        <h1 className="max-w-3xl font-heading text-4xl leading-[1.05] font-extrabold text-balance md:text-6xl">
          Where are we{" "}
          <span className="relative inline-block">
            <span className="relative z-10">off to</span>
            <span className="absolute inset-x-0 bottom-1 -z-0 h-3 -rotate-1 rounded-sm bg-primary/70 md:h-4" aria-hidden />
          </span>{" "}
          today?
        </h1>
        <p className="max-w-xl leading-relaxed text-pretty text-muted-foreground">
          Playgrounds, museums, soft play, zoos and more. Pick a type, or let the dice decide and get out the door.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={surprise}
            disabled={rolling || results.length === 0}
            className="group flex items-center gap-2.5 rounded-full bg-primary px-6 py-3 font-heading text-base font-extrabold text-primary-foreground shadow-[0_6px_0_0] shadow-primary/40 transition hover:-translate-y-0.5 active:translate-y-1 active:shadow-none disabled:opacity-60"
          >
            <Dices className={cn("size-5 transition", rolling ? "animate-spin" : "group-hover:rotate-45")} aria-hidden />
            {rolling ? "Rollingâ€¦" : "Surprise me"}
          </button>

        </div>
      </header>

      <LocationControls />
      {feed.loading && <p role="status">Finding nearby venues…</p>}
      {feed.error && <p role="alert">{feed.error} <button onClick={feed.retry} className="underline">Retry</button></p>}

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

      <div ref={spotlightRef} className="scroll-mt-28">
        {pick && (
          <VenueSpotlight
            venue={pick.venue}
            distance={pick.distance}
            rolling={rolling}
            onReroll={surprise}
            onClose={() => {
              stopSpin()
              setRolling(false)
              setPick(null)
            }}
          />
        )}
      </div>

      <CategoryRail categories={categories} total={categories.reduce((sum,c)=>sum+Number(c.count),0)} selected={category} onSelect={setCategory} />

      <div className="sticky top-[69px] z-20 -mx-4 flex flex-col gap-3 border-b border-border/60 bg-background/85 px-4 py-3 backdrop-blur-md lg:top-0 lg:mx-0 lg:px-0">
        <label className="relative block">
          <span className="sr-only">Search venues</span>
          <Search className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by venue name"
            className="h-12 w-full rounded-full border bg-card pr-4 pl-11 text-base text-foreground placeholder:text-muted-foreground focus-visible:outline-2 focus-visible:outline-ring"
          />
        </label>
        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Filters">
          {TOGGLES.map((t) => (
            <button
              key={t.key}
              type="button"
              aria-pressed={toggles.has(t.key)}
              onClick={() => toggle(t.key)}
              className={cn(
                "rounded-full border px-3.5 py-1.5 text-sm font-bold transition",
                toggles.has(t.key) ? "border-accent bg-accent text-accent-foreground" : "bg-card text-foreground hover:bg-muted",
              )}
            >
              {t.label}
            </button>
          ))}
          {filtered && (
            <button
              type="button"
              onClick={clear}
              className="flex items-center gap-1 rounded-full px-2 py-1.5 text-sm font-semibold text-muted-foreground hover:text-foreground"
            >
              <X className="size-3.5" aria-hidden />
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="flex items-baseline justify-between gap-3">
        <h2 className="font-heading text-2xl font-extrabold">{heading}</h2>
        <p className="text-sm font-semibold text-muted-foreground" aria-live="polite">
          {total} {total === 1 ? "place" : "places"}
          {coords ? ", nearest first" : ""}
        </p>
      </div>

      {!enabled || (feed.loading&&!results.length) || feed.error ? null : results.length > 0 ? (
        <ul className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {results.map(({ venue, distance }, i) => (
            <li key={venue.id}>
              <VenueCard venue={venue} distance={distance} index={i} />
              {coords && distance == null && <p className="text-sm text-muted-foreground">Distance unavailable</p>}
            </li>
          ))}
        </ul>
      ) : (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed bg-card px-6 py-12 text-center">
          <Dices className="size-8 text-primary" aria-hidden />
          <p className="font-heading text-lg font-bold">Nothing matches those filters</p>
          <p className="text-sm text-muted-foreground">Try a different type or clear the filters.</p>
          <button type="button" onClick={clear} className="rounded-full bg-primary px-4 py-2 text-sm font-bold text-primary-foreground">
            Clear filters
          </button>
        </div>
      )}
      {hasMore && <button type="button" onClick={()=>feed.loadMore(currentVenues.length)} disabled={feed.loading} className="mx-auto rounded-full border px-5 py-3 font-semibold disabled:opacity-50">{feed.loading?'Loading…':'Load more'}</button>}
    </div>
  )
}


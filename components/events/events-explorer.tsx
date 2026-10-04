"use client"

import { useEffect, useMemo, useState } from "react"
import { useLocation } from "@/components/location-provider"
import { useDirectoryPage } from "@/hooks/use-directory-page"
import { Search, X } from "lucide-react"
import { EventCard } from "@/components/event-card"
import { addDays } from "@/lib/dates"
import { EVENT_CATEGORIES, eventCategory, isFreeEvent, type EventCategory } from "@/lib/event-meta"
import type { DadEvent } from "@/lib/types"
import { cn } from "@/lib/utils"

type When = "all" | "weekend" | "week"
type Age = "all" | "under5" | "primary" | "older" | "family"

const PAGE_SIZE = 24

const WHEN: { key: When; label: string }[] = [
  { key: "all", label: "Any time" },
  { key: "weekend", label: "This weekend" },
  { key: "week", label: "Next 7 days" },
]

const AGES: { key: Age; label: string }[] = [
  { key: "all", label: "Any age" },
  { key: "under5", label: "Under 5" },
  { key: "primary", label: "5â€“11" },
  { key: "older", label: "12+" },
  { key: "family", label: "Whole family" },
]

const chip = (active: boolean) =>
  cn(
    "flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-semibold transition",
    active
      ? "border-navy bg-navy text-navy-foreground dark:border-primary dark:bg-primary dark:text-primary-foreground"
      : "bg-card text-foreground hover:bg-muted",
  )

const monthFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", month: "long", year: "numeric" })

type Props = { events: DadEvent[]; today: string; saturday: string; sunday: string }

function numbers(value: string) {
  return [...value.matchAll(/\b(\d{1,2})\b/g)].map((match) => Number(match[1])).filter((n) => n <= 18)
}

function matchesAge(event: DadEvent, age: Age) {
  if (age === "all") return true
  const value = (event.age_range ?? "").toLowerCase()
  if (!value) return false
  if (age === "family") return /all ages|whole family|famil(?:y|ies)|all children/.test(value)
  if (age === "under5" && /baby|babies|toddler|pre-?school|under\s*5/.test(value)) return true
  if (age === "older" && /teen|12\s*\+|13\s*\+|14\s*\+|15\s*\+|16\s*\+/.test(value)) return true

  const ages = numbers(value)
  if (!ages.length) return false
  const min = Math.min(...ages)
  const max = /\+/.test(value) && ages.length === 1 ? 18 : Math.max(...ages)
  if (age === "under5") return min <= 4
  if (age === "primary") return min <= 11 && max >= 5
  if (age === "older") return max >= 12
  return true
}

export function EventsExplorer({ events, today, saturday, sunday }: Props) {
  const {coords,browseAll}=useLocation()
  const enabled=Boolean(coords)||browseAll
  const params=new URLSearchParams()
  if(coords){params.set('lat',String(coords.lat));params.set('lng',String(coords.lng))}
  const feed=useDirectoryPage<{events:DadEvent[]}>('/api/events?'+params,enabled)
  const currentEvents=feed.pages[0]?.events??[]
  const [query, setQuery] = useState("")
  const [when, setWhen] = useState<When>("all")
  const [category, setCategory] = useState<EventCategory | "all">("all")
  const [age, setAge] = useState<Age>("all")
  const [freeOnly, setFreeOnly] = useState(false)
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

  const withCategory = useMemo(() => currentEvents.map((event) => ({ event, category: eventCategory(event) })), [currentEvents])

  const categoryCounts = useMemo(() => {
    const counts = new Map<EventCategory, number>()
    for (const { category: c } of withCategory) counts.set(c, (counts.get(c) ?? 0) + 1)
    return EVENT_CATEGORIES.filter((c) => counts.has(c.key)).map((c) => ({ ...c, count: counts.get(c.key)! }))
  }, [withCategory])

  const weekEnd = addDays(today, 7)
  const ends = (e: DadEvent) => (e.end_date ?? e.start_date).slice(0, 10)
  const starts = (e: DadEvent) => e.start_date.slice(0, 10)

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase()
    return withCategory
      .filter(({ category: c }) => category === "all" || c === category)
      .filter(({ event }) => !freeOnly || isFreeEvent(event.cost_text))
      .filter(({ event }) => matchesAge(event, age))
      .filter(({ event }) => when !== "weekend" || (starts(event) <= sunday && ends(event) >= saturday))
      .filter(({ event }) => when !== "week" || starts(event) <= weekEnd)
      .filter(
        ({ event }) =>
          !q || [event.title, event.location, event.description, event.age_range].some((s) => s?.toLowerCase().includes(q)),
      )
      .map(({ event }) => event)
  }, [withCategory, category, freeOnly, age, when, query, saturday, sunday, weekEnd])

  useEffect(() => setVisibleCount(PAGE_SIZE), [query, when, category, age, freeOnly, coords])

  const groups = useMemo(() => {
    if(coords)return [["Nearest events",matches.slice(0,visibleCount)]] as [string,DadEvent[]][]
    const buckets = new Map<string, DadEvent[]>()
    const push = (label: string, event: DadEvent) => buckets.set(label, [...(buckets.get(label) ?? []), event])
    for (const event of matches.slice(0, visibleCount)) {
      if (starts(event) <= today) push("On today", event)
      else if (starts(event) <= sunday && ends(event) >= saturday) push("This weekend", event)
      else if (starts(event) <= weekEnd) push("Later this week", event)
      else push(monthFmt.format(new Date(`${starts(event)}T00:00:00Z`)), event)
    }
    return [...buckets.entries()]
  }, [matches, visibleCount, today, saturday, sunday, weekEnd, coords])

  const filtered = query !== "" || when !== "all" || category !== "all" || age !== "all" || freeOnly
  const clear = () => {
    setQuery("")
    setWhen("all")
    setCategory("all")
    setAge("all")
    setFreeOnly(false)
  }

  let cardIndex = 0
  const canLoadMore = visibleCount < matches.length

  return (
    <div className="flex flex-col gap-8">
      {feed.loading && <p role="status">Finding nearby events…</p>}
      {feed.error && <p role="alert">{feed.error} <button onClick={feed.retry} className="underline">Retry</button></p>}
      <div className="sticky top-[69px] z-20 -mx-4 flex flex-col gap-3 border-b border-border/60 bg-background/85 px-4 py-3 backdrop-blur-md lg:top-0 lg:mx-0 lg:px-0">
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <label className="relative flex-1">
            <span className="sr-only">Search events</span>
            <Search className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by event or age"
              className="h-11 w-full rounded-full border bg-card pr-4 pl-10 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </label>
          <div className="flex gap-2 overflow-x-auto" role="group" aria-label="When">
            {WHEN.map((w) => (
              <button key={w.key} type="button" aria-pressed={when === w.key} onClick={() => setWhen(w.key)} className={chip(when === w.key)}>
                {w.label}
              </button>
            ))}
            <button type="button" aria-pressed={freeOnly} onClick={() => setFreeOnly((v) => !v)} className={chip(freeOnly)}>
              Free only
            </button>
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Age range">
          {AGES.map((item) => (
            <button key={item.key} type="button" aria-pressed={age === item.key} onClick={() => setAge(item.key)} className={chip(age === item.key)}>
              {item.label}
            </button>
          ))}
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1" role="group" aria-label="Event type">
          <button type="button" aria-pressed={category === "all"} onClick={() => setCategory("all")} className={chip(category === "all")}>
            Everything
          </button>
          {categoryCounts.map((c) => (
            <button
              key={c.key}
              type="button"
              aria-pressed={category === c.key}
              onClick={() => setCategory(c.key)}
              className={chip(category === c.key)}
            >
              {c.label}
              <span className="text-xs opacity-70">{c.count}</span>
            </button>
          ))}
        </div>
      </div>

      <p role="status" aria-live="polite" className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
        <span>
          <span className="font-bold text-foreground">{matches.length}</span> {matches.length === 1 ? "event" : "events"}
          {filtered ? " match your filters" : " coming up"}
        </span>
        {matches.length > 0 && <span>Showing {Math.min(visibleCount, matches.length)}</span>}
        {filtered && (
          <button type="button" onClick={clear} className="flex items-center gap-1 font-semibold text-primary hover:underline">
            <X className="size-3.5" aria-hidden />
            Clear filters
          </button>
        )}
      </p>

      {!enabled || feed.loading || feed.error ? null : matches.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed bg-card px-6 py-14 text-center">
          <p className="font-heading text-xl font-bold">Nothing on for that one.</p>
          <p className="max-w-sm leading-relaxed text-muted-foreground">
            Try a different day, age or type. Worst case, there&apos;s always the park and a flask of tea.
          </p>
        </div>
      ) : (
        <>
          {groups.map(([label, items]) => (
            <section key={label} aria-labelledby={`events-${label}`} className="flex flex-col gap-4">
              <h2 id={`events-${label}`} className="flex items-baseline gap-3 font-heading text-2xl font-extrabold">
                {label}
                <span className="text-sm font-semibold text-muted-foreground">{items.length}</span>
              </h2>
              <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((event) => (
                  <li key={event.id}>
                    <EventCard event={event} index={cardIndex++} showCategory />
                    {coords && event.distance_miles == null && <p className="text-sm text-muted-foreground">Distance unavailable</p>}
                  </li>
                ))}
              </ul>
            </section>
          ))}

          {canLoadMore && (
            <div className="flex justify-center pt-2">
              <button
                type="button"
                onClick={() => setVisibleCount((count) => count + PAGE_SIZE)}
                className="rounded-full bg-navy px-6 py-3 text-sm font-bold text-navy-foreground transition hover:-translate-y-0.5 hover:shadow-lg"
              >
                Load 24 more
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

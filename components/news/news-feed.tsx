"use client"

import { useCallback, useEffect, useState } from "react"
import useSWRInfinite from "swr/infinite"
import { LoaderCircle, LocateFixed, MapPin, Newspaper, Zap } from "lucide-react"
import { EmptyState } from "@/components/empty-state"
import { useRegionFromLocation } from "@/hooks/use-region-from-location"
import { cn } from "@/lib/utils"
import {
  CATEGORIES,
  PAGE_SIZE,
  REGIONS,
  fetchNews,
  isRegion,
  type CategoryFilter,
  type NewsItem,
  type RegionFilter,
} from "@/lib/news"
import { NewsCard } from "./news-card"
import { NewsSkeleton } from "./news-skeleton"

/** Where the chosen region is remembered in the browser. */
const REGION_STORAGE_KEY = "dadspace:news-region"

type Key = readonly ["news", RegionFilter, CategoryFilter, number]

/**
 * The interactive part of the News page: region dropdown, category chips,
 * the list of articles and the "Load more" button.
 *
 * `initialItems` is the first page for "All UK" + "All", fetched on the server so
 * the page appears instantly. Changing a filter fetches fresh results.
 */
export function NewsFeed({ initialItems }: { initialItems: NewsItem[] | null }) {
  const [region, setRegion] = useState<RegionFilter>("all")
  const [category, setCategory] = useState<CategoryFilter>("all")

  // Restore the region the dad picked last time.
  useEffect(() => {
    const saved = window.localStorage.getItem(REGION_STORAGE_KEY)
    if (isRegion(saved)) setRegion(saved)
  }, [])

  const changeRegion = useCallback((value: string) => {
    if (!isRegion(value)) return
    setRegion(value)
    window.localStorage.setItem(REGION_STORAGE_KEY, value)
  }, [])

  const { locate, status: locationStatus, message: locationMessage } = useRegionFromLocation(changeRegion)

  // Each "page" is 20 articles. Stop asking for more once a page comes back short.
  const getKey = (pageIndex: number, previousPage: NewsItem[] | null): Key | null => {
    if (previousPage && previousPage.length < PAGE_SIZE) return null
    return ["news", region, category, pageIndex] as const
  }

  const isDefaultView = region === "all" && category === "all"

  const { data, error, size, setSize, isLoading, isValidating, mutate } = useSWRInfinite(
    getKey,
    ([, r, c, page]: Key) => fetchNews({ region: r, category: c, page }),
    {
      fallbackData: isDefaultView && initialItems ? [initialItems] : undefined,
      revalidateFirstPage: false,
      revalidateOnFocus: false,
    },
  )

  const items = data?.flat() ?? []
  const lastPage = data?.[data.length - 1]
  const hasMore = Boolean(lastPage && lastPage.length === PAGE_SIZE)
  const isLoadingMore = isValidating && size > 1 && data?.[size - 1] === undefined

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="flex items-center gap-2 text-sm font-bold tracking-wide text-primary uppercase">
          <Newspaper className="size-4" aria-hidden="true" />
          The dad briefing
        </p>
        <h1 className="font-heading text-4xl font-extrabold tracking-tight text-balance md:text-5xl">News for dads</h1>
        <p className="max-w-2xl leading-relaxed text-muted-foreground text-pretty">
          Two weeks of news that actually matters to you, each with a quick{" "}
          <span className="inline-flex items-center gap-1 font-semibold text-foreground">
            <Zap className="size-3.5 fill-highlight text-highlight" aria-hidden="true" />
            why it matters
          </span>{" "}
          so you can skim it in the time it takes the kettle to boil.
        </p>
      </header>

      <div className="sticky top-[69px] z-20 -mx-4 flex items-center gap-2 border-b border-border/60 bg-background/80 px-4 py-3 backdrop-blur-md lg:top-0 lg:mx-0 lg:rounded-b-xl lg:px-0">
        <div className="flex shrink-0 items-center gap-1 rounded-full border bg-card p-1">
          <label htmlFor="news-region" className="sr-only">
            Region
          </label>
          <div className="relative flex items-center">
            <MapPin className="pointer-events-none absolute left-2.5 size-4 text-accent" aria-hidden="true" />
            <select
              id="news-region"
              value={region}
              onChange={(e) => changeRegion(e.target.value)}
              className="h-9 cursor-pointer appearance-none rounded-full bg-transparent pr-3 pl-8 text-sm font-semibold text-card-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {REGIONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={locate}
            disabled={locationStatus === "locating"}
            aria-label="Use my location to set the region"
            title="Use my location"
            className="flex size-9 shrink-0 items-center justify-center rounded-full text-card-foreground transition hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
          >
            {locationStatus === "locating" ? (
              <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              <LocateFixed className="size-4" aria-hidden="true" />
            )}
          </button>
        </div>

        <span aria-hidden="true" className="h-6 w-px shrink-0 bg-border" />

        <div role="group" aria-label="Filter by topic" className="flex min-w-0 flex-1 gap-2 overflow-x-auto [scrollbar-width:none]">
          {CATEGORIES.map((c) => {
            const active = c.value === category
            return (
              <button
                key={c.value}
                type="button"
                aria-pressed={active}
                onClick={() => setCategory(c.value)}
                className={cn(
                  "h-9 shrink-0 rounded-full border px-4 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring active:scale-95",
                  active
                    ? "border-primary bg-primary text-primary-foreground shadow-md shadow-primary/30"
                    : "border-border bg-card/60 text-card-foreground hover:border-primary/50 hover:bg-card",
                )}
              >
                {c.label}
              </button>
            )
          })}
        </div>
      </div>

      <p role="status" aria-live="polite" className={cn("-mt-3 text-sm leading-relaxed text-muted-foreground", !locationMessage && "sr-only")}>
        {locationStatus === "locating" ? "Finding your region…" : locationMessage}
      </p>

      <section aria-label="Articles" aria-busy={isLoading} className="flex flex-col gap-4">
        {error && !items.length ? (
          <div role="alert" className="flex flex-col items-center gap-3 rounded-lg border border-dashed px-6 py-10 text-center">
            <p className="font-heading text-lg font-bold">{"We couldn't load the news."}</p>
            <p className="text-sm leading-relaxed text-muted-foreground">Check your connection and give it another go.</p>
            <button
              type="button"
              onClick={() => mutate()}
              className="h-11 rounded-full bg-primary px-6 font-semibold text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              Try again
            </button>
          </div>
        ) : !data ? (
          <>
            <span className="sr-only" role="status">
              Loading articles
            </span>
            <NewsSkeleton />
          </>
        ) : !items.length ? (
          <EmptyState title="Nothing new here yet, check back soon." body="Try another topic or region in the meantime." />
        ) : (
          <>
            <NewsCard item={items[0]} variant="hero" priority />

            {items.length > 1 && (
              <ul className="grid gap-4 md:grid-cols-2">
                {items.slice(1).map((item, index) => {
                  // Every fifth card goes wide across both columns to break up the grid.
                  const wide = index % 5 === 4
                  return (
                    <li key={item.id} className={cn(wide && "md:col-span-2")}>
                      <NewsCard item={item} variant={wide ? "wide" : "tile"} />
                    </li>
                  )
                })}
              </ul>
            )}

            {error && (
              <p role="alert" className="text-center text-sm text-muted-foreground">
                {"Couldn't load more articles. Try again below."}
              </p>
            )}

            {(hasMore || error) && (
              <button
                type="button"
                onClick={() => (error ? mutate() : setSize(size + 1))}
                disabled={isLoadingMore}
                className="mx-auto h-12 rounded-full border bg-card px-8 font-semibold text-card-foreground transition hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
              >
                {isLoadingMore ? "Loading…" : error ? "Try again" : "Load more"}
              </button>
            )}
          </>
        )}
      </section>
    </div>
  )
}

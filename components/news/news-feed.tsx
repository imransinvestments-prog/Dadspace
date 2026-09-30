"use client"

import { useEffect, useState } from "react"
import useSWRInfinite from "swr/infinite"
import { EmptyState } from "@/components/empty-state"
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

  function changeRegion(value: string) {
    if (!isRegion(value)) return
    setRegion(value)
    window.localStorage.setItem(REGION_STORAGE_KEY, value)
  }

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
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="font-heading text-3xl font-extrabold tracking-tight text-balance md:text-4xl">News for dads</h1>
          <p className="leading-relaxed text-muted-foreground text-pretty">
            The last two weeks of news that matters to dads, in a sentence or two.
          </p>
        </div>
        <label className="flex flex-col gap-1 text-sm font-semibold">
          Region
          <select
            value={region}
            onChange={(e) => changeRegion(e.target.value)}
            className="h-11 min-w-44 rounded-full border bg-card px-4 text-base font-medium text-card-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {REGIONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </label>
      </header>

      <div
        role="group"
        aria-label="Filter by topic"
        className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] md:mx-0 md:flex-wrap md:px-0"
      >
        {CATEGORIES.map((c) => {
          const active = c.value === category
          return (
            <button
              key={c.value}
              type="button"
              aria-pressed={active}
              onClick={() => setCategory(c.value)}
              className={cn(
                "h-10 shrink-0 rounded-full border px-4 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                active ? "border-navy bg-navy text-navy-foreground dark:border-primary dark:bg-primary dark:text-primary-foreground" : "bg-card text-card-foreground hover:bg-muted",
              )}
            >
              {c.label}
            </button>
          )
        })}
      </div>

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
            <ul className="flex flex-col gap-3">
              {items.map((item) => (
                <li key={item.id}>
                  <NewsCard item={item} />
                </li>
              ))}
            </ul>

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

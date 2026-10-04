"use client"

import useSWR from "swr"
import { HeroGreeting } from "./hero-greeting"
import { WeekendEvents } from "./weekend-events"
import { TrendingThreads } from "./trending-threads"
import { NewsHeadlines } from "./news-headlines"
import { TopDeal } from "./top-deal"
import { useLocation } from "@/components/location-provider"
import { LocationControls } from "@/components/location-controls"
import type { HomeData } from "@/lib/types"

const fetcher = (url: string) => fetch(url).then((r) => r.json() as Promise<HomeData>)

export function HomeDashboard({ initial }: { initial: HomeData }) {
  const { coords, status, request } = useLocation()
  const key = coords ? `/api/home?lat=${coords.lat}&lng=${coords.lng}` : "/api/home"
  const { data = initial, isValidating } = useSWR(key, fetcher, {
    fallbackData: initial,
    keepPreviousData: true,
    refreshInterval: 60_000,
    revalidateOnFocus: true,
  })

  const sorting = status === "locating" || (!!coords && isValidating && !data.events.nearby)

  return (
    <div className="flex flex-col gap-10">
      <HeroGreeting greeting={data.greeting} sleeps={data.sleepsToWeekend} weekendLabel={data.weekendLabel} />
      <LocationControls />
      <WeekendEvents events={data.events} locationStatus={status} sorting={sorting} onRequestLocation={request} />
      <div className="grid gap-10 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <NewsHeadlines articles={data.articles} />
        </div>
        <TopDeal deal={data.deal} />
      </div>
      <TrendingThreads threads={data.threads} />
    </div>
  )
}

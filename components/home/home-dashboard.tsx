"use client"

import useSWR from "swr"
import { HeroGreeting } from "./hero-greeting"
import { WeekendEvents } from "./weekend-events"
import { TrendingThreads } from "./trending-threads"
import { NewsHeadlines } from "./news-headlines"
import { TopDeal } from "./top-deal"
import type { HomeData } from "@/lib/types"

const fetcher = (url: string) => fetch(url).then((r) => r.json() as Promise<HomeData>)

export function HomeDashboard({ initial }: { initial: HomeData }) {
  const { data = initial } = useSWR("/api/home", fetcher, {
    fallbackData: initial,
    refreshInterval: 60_000,
    revalidateOnFocus: true,
  })

  return (
    <div className="flex flex-col gap-10">
      <HeroGreeting greeting={data.greeting} sleeps={data.sleepsToWeekend} weekendLabel={data.weekendLabel} />
      <WeekendEvents events={data.events} />
      <div className="grid gap-10 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrendingThreads threads={data.threads} />
        </div>
        <TopDeal deal={data.deal} />
      </div>
      <NewsHeadlines articles={data.articles} />
    </div>
  )
}

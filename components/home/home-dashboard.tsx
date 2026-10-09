"use client"

import useSWR from "swr"
import { HeroGreeting } from "./hero-greeting"
import { DadJoke } from "./dad-joke"
import { LocalPlaces } from "./local-places"
import { TrendingThreads } from "./trending-threads"
import { NewsHeadlines } from "./news-headlines"
import { NearbyWeek } from "./nearby-week"
import { HomeDeals } from "./home-deals"
import { useLocation } from "@/components/location-provider"
import type { HomeData } from "@/lib/types"

const fetcher = (url: string) => fetch(url).then((r) => r.json() as Promise<HomeData>)

export function HomeDashboard({ initial }: { initial: HomeData }) {
  const { coords } = useLocation()
  const key = coords ? `/api/home?lat=${coords.lat}&lng=${coords.lng}` : "/api/home"
  const { data = initial } = useSWR(key, fetcher, {
    fallbackData: initial,
    keepPreviousData: true,
    refreshInterval: 60_000,
    revalidateOnFocus: true,
  })


  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <p className="text-xs font-bold tracking-wider text-accent uppercase">Your weekend starts here</p>
        <h1 className="font-heading text-3xl leading-tight font-extrabold tracking-tight text-balance sm:text-4xl xl:text-5xl">Good times. Great dad jokes.</h1>
        <p className="text-base text-muted-foreground sm:text-lg">Days out, news and deals for UK dads.</p>
      </header>
      <div className="grid items-stretch gap-5 md:grid-cols-[minmax(0,1.8fr)_minmax(280px,1fr)] lg:grid-cols-1 xl:grid-cols-[minmax(0,1.8fr)_minmax(280px,1fr)]">
        <HeroGreeting greeting={data.greeting} sleeps={data.sleepsToWeekend} weekendLabel={data.weekendLabel} />
        <DadJoke />
      </div>
      <LocalPlaces />
      <NewsHeadlines monthlyNews={data.monthlyNews} />
      <NearbyWeek />
      <HomeDeals />
      <TrendingThreads threads={data.threads} />
    </div>
  )
}

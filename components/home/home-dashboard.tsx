import Link from "next/link"
import { HeroGreeting } from "./hero-greeting"
import { DadJoke } from "./dad-joke"
import { LocalPlaces } from "./local-places"
import { TrendingThreads } from "./trending-threads"
import { NewsHeadlines } from "./news-headlines"
import { NearbyWeek } from "./nearby-week"
import { HomeDeals } from "./home-deals"
import { WeatherCard } from "./weather-card"
import { weatherConfigured } from "@/lib/weather"
import type { HomeData } from "@/lib/types"
import { FORUM_ENABLED } from "@/lib/launch"
import type { Venue } from "@/lib/venue-meta"
import type { LiveDeal } from "@/lib/deals-selection"

// Server-rendered: the sections that refresh or follow the user's location are client components.
export function HomeDashboard({ data, publicPlaces = [], initialDeals = [], children }: { data: HomeData; publicPlaces?: Venue[]; initialDeals?: LiveDeal[]; children?: React.ReactNode }) {

  return (
    <div className="flex flex-col gap-5 sm:gap-8">
      <header className="flex flex-col gap-3">
        <p className="text-xs font-bold tracking-wider text-accent-ink uppercase">Your weekend starts here</p>
        <h1 className="font-heading text-2xl leading-tight font-extrabold tracking-tight text-balance sm:text-4xl xl:text-5xl">Family days out for UK dads</h1>
        <p className="text-base text-muted-foreground sm:text-lg">Days out, news and deals for UK dads.</p>
      </header>
      <nav aria-label="Explore nearby" className="flex flex-wrap gap-2 sm:hidden">
        {[['/venues','Places nearby'],['/events','Events nearby'],['/activities','Activities nearby']].map(([href,label])=><Link key={href} href={href} className="inline-flex min-h-11 items-center rounded-full border bg-card px-3 text-sm font-semibold">{label}</Link>)}
      </nav>
      <div className="grid items-stretch gap-5 md:grid-cols-[minmax(0,1.8fr)_minmax(280px,1fr)] lg:grid-cols-1 xl:grid-cols-[minmax(0,1.8fr)_minmax(280px,1fr)]">
        <HeroGreeting greeting={data.greeting} sleeps={data.sleepsToWeekend} weekendLabel={data.weekendLabel} />
        <DadJoke />
      </div>
      {/* Decided on the server so an unconfigured card never appears and then collapses. */}
      {weatherConfigured() && <WeatherCard />}
      {children}
      <LocalPlaces publicPlaces={publicPlaces}/>
      <div className="border-t pt-8"><NewsHeadlines monthlyNews={data.monthlyNews} /></div>
      <NearbyWeek />
      <HomeDeals initialDeals={initialDeals}/>
      {FORUM_ENABLED && <TrendingThreads threads={data.threads} />}
    </div>
  )
}

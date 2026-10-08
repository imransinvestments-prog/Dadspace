"use client"
import useSWR from "swr"
import Link from "next/link"
import { useLocation } from "@/components/location-provider"
import { EventCard } from "@/components/event-card"
import { SectionHeader } from "./section-header"
import type { DadEvent } from "@/lib/types"
type Result = {events:DadEvent[];eventsUnavailable:boolean;activityCount:number|null;weekStart:string;weekEnd:string;radiusMiles:number}
const fetcher = async (url:string):Promise<Result> => {const r=await fetch(url);if(!r.ok) throw new Error("Unavailable");return r.json()}
export function NearbyWeek() {
  const {coords}=useLocation()
  const {data,error,isLoading}=useSWR(coords ? `/api/home/nearby-week?lat=${coords.lat}&lng=${coords.lng}` : null,fetcher,{refreshInterval:300000})
  return <section aria-labelledby="nearby-title" className="flex flex-col gap-4">
    <SectionHeader id="nearby-title" title="What's on nearby" href="/events" linkLabel="All events"/>
    <p className="text-sm text-muted-foreground">The two closest upcoming events, plus activities happening this week.</p>
    <div className="grid gap-4 md:grid-cols-3">
      {data?.events.map(event=><EventCard key={event.id} event={event} showCategory/>)}
      {(!data?.events.length) && <p className="rounded-xl border bg-card p-5 md:col-span-2">{isLoading ? "Finding your closest events…" : !coords ? "Set your location to discover nearby events." : error || data?.eventsUnavailable ? "Nearby events are temporarily unavailable." : "No upcoming events found nearby."}</p>}
      <Link href="/activities" className="flex flex-col justify-center gap-4 rounded-xl bg-navy p-6 text-navy-foreground">
        <span className="text-sm font-bold uppercase tracking-wide">This week near you</span>
        <span className="font-heading text-6xl font-extrabold">{data?.activityCount != null ? data.activityCount : "—"}</span>
        <h3 className="font-heading text-xl font-bold">Local activities</h3>
        <p className="text-sm opacity-80">{data?.activityCount != null ? "Within 30 miles · includes recurring activities" : isLoading ? "Counting local activities…" : "Activity count currently unavailable."}</p>
        {data && <p className="text-xs opacity-80">{data.weekStart} – {data.weekEnd}</p>}
        <span className="font-semibold">Explore activities →</span>
      </Link>
    </div>
  </section>
}

"use client"
import useSWR from "swr"
import { CloudSun } from "lucide-react"
import { DEFAULT_LOCATION, useLocation } from "@/components/location-provider"
import type { DayForecast } from "@/lib/weather"

type Result =
  | { status: "ok"; approximate: boolean; area: string | null; days: DayForecast[] }
  | { status: "no_location" | "unavailable" | "not_configured" }

const fetcher = async (url: string): Promise<Result> => {
  const response = await fetch(url)
  if (!response.ok && response.status !== 503) throw new Error("Unavailable")
  return response.json()
}

export function WeatherCard() {
  const { coords, label } = useLocation()
  // The untouched default is not the visitor's choice, so let the server use a rough IP area instead.
  const chosen = coords && (coords.lat !== DEFAULT_LOCATION.lat || coords.lng !== DEFAULT_LOCATION.lng)
  const { data, error } = useSWR(chosen ? `/api/home/weather?lat=${coords.lat}&lng=${coords.lng}` : "/api/home/weather", fetcher,
    { revalidateOnFocus: false, dedupingInterval: 600_000 })
  if (data?.status === "not_configured") return null
  const where = data?.status === "ok" ? (data.approximate ? (data.area ? `near ${data.area} (approximate)` : "near you (approximate)") : `near ${label}`) : null

  // Every state has the same rows and height, so the forecast arriving never shifts the page:
  // one header line, one "near" line and one-line cells (the summary truncates).
  return (
    <section aria-labelledby="weather-title" className="flex h-48 flex-col gap-2 rounded-xl border bg-card p-4 sm:p-5">
      <div className="flex items-center justify-between gap-2">
        <h2 id="weather-title" className="flex items-center gap-2 font-heading text-lg font-bold">
          <CloudSun className="size-5 text-accent" aria-hidden />
          Weekend weather
        </h2>
        <a href="https://www.metoffice.gov.uk/" className="shrink-0 text-xs text-muted-foreground underline underline-offset-2">Forecast: Met Office</a>
      </div>
      <p className="truncate text-sm text-muted-foreground">{where ?? " "}</p>
      {data?.status === "ok" ? (
        <ul className="grid grid-cols-3 gap-2">
          {data.days.map(day => (
            <li key={day.date} className="min-w-0 rounded-lg bg-muted/50 p-2 text-sm">
              <p className="font-semibold">{day.label}</p>
              <p className="truncate text-muted-foreground" title={day.summary ?? undefined}>{day.summary ?? "Unclear"}</p>
              <p>{day.max !== null ? `${day.max}°` : "–"}<span className="text-muted-foreground"> / {day.min !== null ? `${day.min}°` : "–"}</span><span className="sr-only"> Celsius, high and low</span></p>
              <p className="text-muted-foreground">{day.rainChance !== null ? <>Rain {day.rainChance}%<span className="sr-only"> chance</span></> : " "}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p role="status" className="text-sm text-muted-foreground">
          {error || data?.status === "unavailable" ? "The forecast is temporarily unavailable." :
            data?.status === "no_location" ? "Set your location to see the forecast." : "Loading the forecast…"}
        </p>
      )}
    </section>
  )
}

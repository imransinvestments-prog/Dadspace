import "server-only"
import { unstable_cache } from "next/cache"
import { londonToday, upcomingWeekend, weekday } from "./dates"
import type { Point } from "./distance"

const ENDPOINT = "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily"
// The free plan allows 360 calls a day. Sharing one forecast per 0.25° cell (~28 km)
// for three hours keeps a busy day well inside it; daily values change slowly.
const GRID = 0.25
const REVALIDATE_SECONDS = 3 * 3600
const DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

// Met Office significant weather codes; 4 is not used.
const SUMMARIES: Record<number, string> = {
  0: "Clear", 1: "Sunny", 2: "Partly cloudy", 3: "Partly cloudy", 5: "Mist", 6: "Fog", 7: "Cloudy", 8: "Overcast",
  9: "Light showers", 10: "Light showers", 11: "Drizzle", 12: "Light rain", 13: "Heavy showers", 14: "Heavy showers",
  15: "Heavy rain", 16: "Sleet showers", 17: "Sleet showers", 18: "Sleet", 19: "Hail showers", 20: "Hail showers",
  21: "Hail", 22: "Light snow showers", 23: "Light snow showers", 24: "Light snow", 25: "Heavy snow showers",
  26: "Heavy snow showers", 27: "Heavy snow", 28: "Thundery showers", 29: "Thundery showers", 30: "Thunder",
}

export type DayForecast = { date: string; label: string; summary: string | null; max: number | null; min: number | null; rainChance: number | null }
type Daily = { date: string; dayCode: number | null; nightCode: number | null; max: number | null; min: number | null; dayRain: number | null; nightRain: number | null }

export function weatherConfigured() {
  return !!process.env.MET_OFFICE_DATAHUB_API_KEY
}

export function gridPoint(point: Point): Point {
  const snap = (value: number) => Math.round(Math.round(value / GRID) * GRID * 100) / 100
  return { lat: snap(point.lat), lng: snap(point.lng) }
}

const num = (value: unknown) => typeof value === "number" && Number.isFinite(value) ? value : null

export function parseDaily(body: unknown): Daily[] {
  const series = (body as { features?: { properties?: { timeSeries?: unknown } }[] })?.features?.[0]?.properties?.timeSeries
  if (!Array.isArray(series)) throw new Error("Unexpected Met Office response")
  return series.flatMap(row => {
    const r = row as Record<string, unknown>
    if (typeof r.time !== "string" || !/^\d{4}-\d{2}-\d{2}/.test(r.time)) return []
    return [{ date: r.time.slice(0, 10), dayCode: num(r.daySignificantWeatherCode), nightCode: num(r.nightSignificantWeatherCode),
      max: num(r.dayMaxScreenTemperature), min: num(r.nightMinScreenTemperature),
      dayRain: num(r.dayProbabilityOfPrecipitation), nightRain: num(r.nightProbabilityOfPrecipitation) }]
  })
}

/** Today plus the coming weekend, never a past day; a missing day is left out rather than guessed. */
export function selectDays(daily: Daily[], today = londonToday()): DayForecast[] {
  const { saturday, sunday } = upcomingWeekend(today)
  const wanted = [...new Set([today, saturday, sunday])].filter(date => date >= today)
  return wanted.flatMap(date => {
    const day = daily.find(d => d.date === date)
    if (!day) return []
    // Late in the day the daytime values can be absent, so fall back to the night ones.
    const code = day.dayCode ?? day.nightCode
    const round = (value: number | null) => value === null ? null : Math.round(value)
    return [{ date, label: date === today ? "Today" : DAY_NAMES[weekday(date)], summary: code === null ? null : SUMMARIES[code] ?? null,
      max: round(day.max), min: round(day.min), rainChance: round(day.dayRain ?? day.nightRain) }]
  })
}

// Throws on any failure so an outage or a rate limit is retried later, never cached.
const readDaily = unstable_cache(async (lat: number, lng: number): Promise<Daily[]> => {
  const key = process.env.MET_OFFICE_DATAHUB_API_KEY
  if (!key) throw new Error("Weather is not configured")
  const params = new URLSearchParams({ latitude: String(lat), longitude: String(lng), excludeParameterMetadata: "true", includeLocationName: "false" })
  const response = await fetch(`${ENDPOINT}?${params}`, { headers: { apikey: key, accept: "application/json" }, cache: "no-store", signal: AbortSignal.timeout(8000) })
  if (!response.ok) throw new Error(`Met Office HTTP ${response.status}`)
  return parseDaily(await response.json())
}, ["met-office-daily-v1"], { revalidate: REVALIDATE_SECONDS })

export async function forecastDays(point: Point): Promise<DayForecast[]> {
  const cell = gridPoint(point)
  return selectDays(await readDaily(cell.lat, cell.lng))
}

const LONDON = "Europe/London"

export function londonToday(now = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: LONDON }).format(now)
}

export function londonHour(now = new Date()): number {
  return Number(new Intl.DateTimeFormat("en-GB", { timeZone: LONDON, hour: "numeric", hour12: false }).format(now))
}

function toUtcDate(isoDay: string) {
  return new Date(`${isoDay.slice(0, 10)}T00:00:00Z`)
}

export function addDays(isoDay: string, days: number): string {
  const d = toUtcDate(isoDay)
  d.setUTCDate(d.getUTCDate() + days)
  return d.toISOString().slice(0, 10)
}

/** 0 = Sunday ... 6 = Saturday */
export function weekday(isoDay: string): number {
  return toUtcDate(isoDay).getUTCDay()
}

export function upcomingWeekend(today = londonToday()) {
  const day = weekday(today)
  if (day === 6) return { saturday: today, sunday: addDays(today, 1), sleeps: 0 }
  if (day === 0) return { saturday: addDays(today, -1), sunday: today, sleeps: 0 }
  const sleeps = 6 - day
  return { saturday: addDays(today, sleeps), sunday: addDays(today, sleeps + 1), sleeps }
}

const dayFmt = new Intl.DateTimeFormat("en-GB", { timeZone: "UTC", weekday: "short", day: "numeric", month: "short" })

export function formatEventDate(start: string, end?: string | null): string {
  const s = start.slice(0, 10)
  const e = end?.slice(0, 10)
  if (!e || e === s) return dayFmt.format(toUtcDate(s))
  return `${dayFmt.format(toUtcDate(s))} – ${dayFmt.format(toUtcDate(e))}`
}

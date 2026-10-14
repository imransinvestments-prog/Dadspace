export type Run = {
  id: number; event: string; status: string; conclusion: string | null
  created_at: string; updated_at: string; html_url: string
}
export type Job = { name: string; status: string; conclusion: string | null; completed_at: string | null }
export type Observation = { run: Run; jobs: Job[] | null }

export const FEEDS = [
  { key: "news / news", label: "News", issue: 35 },
  { key: "venue_reference / sync", label: "Venue reference", issue: 34 },
  { key: "civic / collect", label: "Civic events", issue: 39 },
  { key: "activities / collect", label: "Activities", issue: 39 },
  { key: "deals / collect", label: "Deals", issue: 48 },
]

export function feedHealth(observations: Observation[], key: string, now = new Date()) {
  const runs = observations.filter(item => item.run.event === "schedule")
    .sort((a, b) => Date.parse(b.run.created_at) - Date.parse(a.run.created_at))
  const latest = runs[0]
  const latestJob = latest?.jobs?.find(job => job.name === key)
  const successful = runs.find(item => item.jobs?.some(job => job.name === key && job.conclusion === "success"))
  const successfulJob = successful?.jobs?.find(job => job.name === key && job.conclusion === "success")
  const lastSuccess = successfulJob?.completed_at || null
  // Twelve-hour cadence plus four hours for runner delay/collection.
  const missed = !latest || now.getTime() - Date.parse(latest.run.created_at) > 16 * 3600_000
  let status = "Unknown"
  if (latestJob) {
    status = latestJob.status !== "completed" ? "Running" :
      latestJob.conclusion === "success" ? "Job passed" :
      latestJob.conclusion === "skipped" ? "Skipped" :
      latestJob.conclusion === "cancelled" ? "Cancelled" : "Failed"
  } else if (latest && latest.run.status !== "completed" && latest.jobs !== null) {
    status = "Waiting"
  }
  return { status, missed, lastSuccess, latestAt: latest?.run.created_at || null,
    url: latest?.run.html_url || null }
}

export function nextLondonRun(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(now)
  const part = (name: string) => Number(parts.find(p => p.type === name)!.value)
  const day = Date.UTC(part("year"), part("month") - 1, part("day"))
  for (let offset = 0; offset < 3; offset++) {
    for (const hour of [7, 19]) {
      const candidate = new Date(day + offset * 86400_000 + hour * 3600_000 + 17 * 60_000)
      const localHour = Number(new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", hour: "2-digit", hourCycle: "h23" }).format(candidate))
      candidate.setUTCHours(candidate.getUTCHours() - (localHour - hour))
      if (candidate > now) return candidate.toISOString()
    }
  }
  throw new Error("Unable to determine next collection slot")
}

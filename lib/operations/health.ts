export type Run = {
  id: number; event: string; status: string; conclusion: string | null
  created_at: string; updated_at: string; html_url: string; display_title?: string
}

/** A slot is run either by GitHub's schedule or, on time, by the Supabase timer (#124),
 * whose dispatches are named "timer slot …". Other manual runs are not slot evidence. */
export function isSlotRun(run: Run) {
  return run.event === "schedule" || (run.event === "workflow_dispatch" && /\btimer slot\b/.test(run.display_title ?? ""))
}

/** Slot-based warning, separate from job status and source/publication success.
 * Deadlines approved by the owner on 17 October 2026 under #124.
 * Public GitHub metadata cannot establish why dispatch was late.
 */
export function scheduledSlotHealth(observations: Observation[] | null, key: string, now = new Date(), dispatchMinutes = 60, completionMinutes = 240) {
  let slot = new Date(now.getTime() - 36 * 3600_000)
  for (;;) {
    const next = new Date(nextLondonRun(slot))
    if (next > now) break
    slot = next
  }
  const expectedAt = slot.toISOString()
  if (observations === null) return { expectedAt, signal: "Evidence unavailable", delayMinutes: null }
  const latest = observations.filter(o => isSlotRun(o.run) && Date.parse(o.run.created_at) >= slot.getTime() && Date.parse(o.run.created_at) <= now.getTime())
    .sort((a,b) => Date.parse(a.run.created_at) - Date.parse(b.run.created_at))[0]
  const elapsed = (now.getTime() - slot.getTime()) / 60000
  if (!latest) return { expectedAt, signal: elapsed > dispatchMinutes ? "Missing scheduled dispatch" : "Within dispatch allowance", delayMinutes: null }
  const delayMinutes = Math.floor((Date.parse(latest.run.created_at) - slot.getTime()) / 60000)
  if (latest.jobs === null) return { expectedAt, signal: "Job evidence unavailable", delayMinutes }
  const job = latest.jobs.find(j => j.name === key)
  if (job?.conclusion === "cancelled" || latest.run.conclusion === "cancelled" && !job) return { expectedAt, signal: "Cancelled — inspect feed evidence", delayMinutes }
  if (job?.conclusion === "failure" || job?.conclusion === "timed_out") return { expectedAt, signal: "Feed failed — inspect source evidence", delayMinutes }
  if (job?.conclusion === "skipped") return { expectedAt, signal: "Feed skipped — refresh not established", delayMinutes }
  if (job?.conclusion === "success") return { expectedAt, signal: delayMinutes > dispatchMinutes ? "Late dispatch; job passed" : "Job passed; verify useful supply", delayMinutes }
  return { expectedAt, signal: elapsed > completionMinutes ? "Feed completion overdue" : delayMinutes > dispatchMinutes ? "Late dispatch; collection pending" : "Collection pending", delayMinutes }
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
  const runs = observations.filter(item => isSlotRun(item.run))
    .sort((a, b) => Date.parse(b.run.created_at) - Date.parse(a.run.created_at))
  // A late scheduled duplicate that the gate skipped must not hide the timer's real run.
  const latest = runs.find(item => item.jobs?.find(job => job.name === key)?.conclusion !== "skipped") ?? runs[0]
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

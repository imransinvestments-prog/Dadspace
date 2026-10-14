import "server-only"
import { unstable_cache } from "next/cache"
import { createClient } from "@/lib/supabase/server"
import { isOperationsUser, isVerifiedOperationsEmail } from "./access"
import type { Run, Job, Observation } from "./health"

const API = "https://api.github.com/repos/imransinvestments-prog/Dadspace"
async function github<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" },
    cache: "no-store", signal: AbortSignal.timeout(10_000), redirect: "error",
  })
  if (!response.ok) throw new Error("Operations evidence unavailable")
  return response.json()
}

async function scheduledRuns(workflow: string, limit: number) {
  const data = await github<{ workflow_runs: Run[] }>(`/actions/workflows/${workflow}/runs?branch=main&event=schedule&per_page=${limit}`)
  if (!Array.isArray(data.workflow_runs)) throw new Error("Invalid workflow evidence")
  return data.workflow_runs.filter(run => run.event === "schedule" && Number.isSafeInteger(run.id)).slice(0, limit)
}

async function jobs(run: Run): Promise<Observation> {
  try {
    const data = await github<{ jobs: Job[]; total_count: number }>(`/actions/runs/${run.id}/jobs?per_page=100`)
    if (!Array.isArray(data.jobs) || data.total_count > 100) return { run, jobs: null }
    return { run, jobs: data.jobs }
  } catch { return { run, jobs: null } }
}

// Only public GitHub job metadata is shared. No cookies, auth identities, secrets,
// database rows or logs enter this cache. Seven requests maximum per refresh.
const getPublicEvidence = unstable_cache(async () => {
  const [workers, originals, shadow] = await Promise.allSettled([
    scheduledRuns("daily-workers.yml", 3), scheduledRuns("original-content.yml", 1),
    github<{ workflow_runs: Run[] }>("/actions/workflows/shadow-review.yml/runs?branch=main&event=workflow_run&per_page=1"),
  ])
  const observations = workers.status === "fulfilled" ? await Promise.all(workers.value.map(jobs)) : null
  const original = originals.status === "fulfilled" && originals.value[0] ? await jobs(originals.value[0]) : null
  return { observations, original,
    shadow: shadow.status === "fulfilled" ? shadow.value.workflow_runs?.[0] || null : null,
    fetchedAt: new Date().toISOString() }
}, ["dadspace-operations-public-evidence-v1"], { revalidate: 600 })

export async function getOperationsDashboard() {
  if (!process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL || !process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY) {
    return { access: "unavailable" as const }
  }
  try {
    const client = await createClient()
    const { data, error } = await client.auth.getUser()
    if (error || !data.user) return { access: "sign-in" as const }
    if (data.user.is_anonymous || !(isOperationsUser(data.user.id, process.env.DADSPACE_OPERATOR_USER_IDS) ||
      isVerifiedOperationsEmail(data.user, process.env.DADSPACE_OPERATOR_EMAILS))) return { access: "denied" as const }
    return { access: "allowed" as const, evidence: await getPublicEvidence() }
  } catch { return { access: "unavailable" as const } }
}

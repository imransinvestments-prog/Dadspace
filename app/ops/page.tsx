import Link from "next/link"
import DatabaseEvidence from "./database-evidence"
import { redirect, notFound } from "next/navigation"
import { getOperationsDashboard } from "@/lib/operations/dashboard"
import { feedHealth, FEEDS, nextLondonRun, scheduledSlotHealth } from "@/lib/operations/health"
import { OPERATIONS_PROCESSES } from "@/lib/operations/processes"
import { pageMetadata } from "@/lib/seo"

export const dynamic = "force-dynamic"
export const metadata = pageMetadata("Operations", "/ops", "Dadspace operator dashboard", { noIndex: true })
const time = (value: string | null) => value ? new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Not observed"
const badge = (status: string) => status === "Job passed" ? "bg-emerald-100 text-emerald-900" : ["Failed", "Skipped", "Cancelled"].includes(status) ? "bg-amber-100 text-amber-900" : "bg-muted text-muted-foreground"

export default async function OperationsPage() {
  const result = await getOperationsDashboard()
  if (result.access === "sign-in") redirect("/auth/login?next=%2Fops")
  if (result.access === "denied") notFound()
  if (result.access !== "allowed") return <section className="rounded-3xl border bg-card p-8"><h1 className="text-3xl font-bold">Operations unavailable</h1><p className="mt-3 text-muted-foreground">Operator sign-in could not be verified. Try again later or contact the site owner.</p></section>
  const { evidence } = result
  const now = new Date()
  const original = evidence.original ? feedHealth([evidence.original], "publish", now) : null
  return <div className="flex flex-col gap-8">
    <header className="rounded-3xl bg-primary p-6 text-primary-foreground sm:p-8">
      <p className="text-sm font-semibold opacity-80">DADSPACE UPKEEP</p>
      <h1 className="mt-2 text-3xl font-bold sm:text-4xl">Operations</h1>
      <p className="mt-3 max-w-2xl">Collection status, evidence and the work that needs attention.</p>
      <Link href="/ops/sprint-5" className="mt-4 inline-block font-semibold underline">Sprint 5: consolidated review pack</Link>
      <div className="mt-5 flex flex-wrap gap-3 text-sm"><span className="rounded-full border border-current px-3 py-1">Read-only</span><span className="rounded-full border border-current px-3 py-1">W3 · 10 km · Ages 0–5</span></div>
    </header>
    <nav aria-label="Operations sections" className="flex flex-wrap gap-4 text-sm font-semibold"><a href="#collections" className="underline underline-offset-4">Collections</a><a href="#sources" className="underline underline-offset-4">Source health & review</a><a href="#editorial" className="underline underline-offset-4">Editorial & AI review</a><a href="#processes" className="underline underline-offset-4">Upkeep processes</a></nav>
    <section id="collections" className="scroll-mt-24">
      <h2 className="text-2xl font-bold">Collections</h2>
      <p className="mt-2 text-sm text-muted-foreground">Next expected start: {time(nextLondonRun(now))} UK time. Evidence fetched {time(evidence.fetchedAt)}; refreshes within ten minutes. Runner delays can move actual start times.</p>
      {!evidence.observations && <p role="status" className="mt-4 rounded-xl border p-4">Worker evidence is unavailable. A failed evidence request does not establish a failed or empty feed.</p>}
      <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {FEEDS.map(feed => {
          const health = feedHealth(evidence.observations || [], feed.key, now)
          const slot = scheduledSlotHealth(evidence.observations, feed.key, now)
          return <article key={feed.key} className="rounded-2xl border bg-card p-5">
            <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="font-bold">{feed.label}</h3><span className={`rounded-full px-3 py-1 text-xs font-semibold ${badge(health.status)}`}>{health.status}</span></div>
            {evidence.observations && health.missed && <p className="mt-3 text-sm font-semibold text-amber-800 dark:text-amber-300">No scheduled start observed within 16 hours.</p>}
            <p className="mt-3 text-sm font-semibold">{slot.signal}</p><p className="mt-1 text-xs text-muted-foreground">Expected slot: {time(slot.expectedAt)} UK. Agreed warning allowances: dispatch 60 minutes; completion four hours. Approved 17 October 2026. Dispatch-to-slot association is inferred from timing.</p>
            <dl className="mt-4 space-y-3 text-sm"><div><dt className="text-muted-foreground">Latest scheduled start</dt><dd>{time(health.latestAt)}</dd></div><div><dt className="text-muted-foreground">Last job success in the three-run window</dt><dd>{time(health.lastSuccess)}</dd></div><div><dt className="text-muted-foreground">Source freshness / supply evidence</dt><dd><a href="#sources" className="underline">See source health & review</a></dd></div></dl>
            <div className="mt-5 flex flex-wrap gap-4 text-sm font-semibold">{health.url && <a href={health.url} className="underline underline-offset-4">Run evidence</a>}<a href={`https://github.com/imransinvestments-prog/Dadspace/issues/${feed.issue}`} className="underline underline-offset-4">Delivery ticket</a></div>
          </article>
        })}
      </div>
      <p className="mt-4 text-sm text-muted-foreground">A passed job can contain source failures or zero useful results. This window is not seven-day acceptance. Source signals and national backlog counts are below; pilot quality and publication acceptance remain separate.</p>
    </section>
    <section className="rounded-2xl border bg-card p-6"><h2 className="text-2xl font-bold">Human review desk</h2><p className="mt-3">Review owner decisions, acceptance criteria and evidence, and record follow-up directly against the delivery task.</p><Link href="/ops/reviews" className="mt-4 inline-flex rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground">Review and update tasks</Link></section>
    <DatabaseEvidence />
    <section id="editorial" className="scroll-mt-24 grid gap-4 sm:grid-cols-2">
      <article className="rounded-2xl border bg-card p-6"><h2 className="text-xl font-bold">Originals</h2><p className="mt-3 font-semibold">{original?.status || "Unknown"}</p><p className="mt-2 text-sm text-muted-foreground">Last observed publication-job success: {time(original?.lastSuccess || null)}. Check the run and published post for actual editorial acceptance; duplicate slots can be skipped successfully.</p>{original?.missed && <p className="mt-3 text-sm font-semibold">No recent scheduled start observed.</p>}<div className="mt-4 flex gap-4 text-sm font-semibold">{original?.url && <a className="underline" href={original.url}>Run evidence</a>}<Link className="underline" href="/originals">Published posts</Link></div></article>
      <article className="rounded-2xl border bg-card p-6"><h2 className="text-xl font-bold">Provider shadow review</h2><p className="mt-3 font-semibold">{evidence.shadow ? evidence.shadow.status === "completed" ? evidence.shadow.conclusion || "Unknown" : "Running" : "Unknown"}</p><p className="mt-2 text-sm text-muted-foreground">Gemini remains the production default. Shadow comparisons do not publish. Failed or incomplete responses cannot establish provider quality or savings. Token and billed-cost data are not connected here yet.</p>{evidence.shadow && <a className="mt-4 inline-block text-sm font-semibold underline" href={evidence.shadow.html_url}>Comparison evidence</a>}</article>
    </section>
    <section id="processes" className="scroll-mt-24"><h2 className="text-2xl font-bold">Upkeep processes</h2><p className="mt-2 text-sm text-muted-foreground">Job visibility, source signals and read-only evidence queues are connected. Review decisions and maintenance controls remain pending; each dependency is listed below.</p>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">{OPERATIONS_PROCESSES.map(process => <article key={process.name} className="rounded-2xl border bg-card p-5"><h3 className="font-bold">{process.name}</h3><p className="mt-2 text-sm text-muted-foreground">{process.owner} · {process.permission}</p><p className="mt-3 text-sm">{process.cadence}</p><p className="mt-3 text-sm"><strong>Evidence:</strong> {process.evidence}</p><p className="mt-3 text-sm"><strong>Next:</strong> {process.next}</p><a href={process.href} className="mt-4 inline-block text-sm font-semibold underline underline-offset-4">Evidence and recovery work · #{process.issue}</a></article>)}</div>
    </section>
  </div>
}

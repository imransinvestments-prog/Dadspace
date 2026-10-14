import Link from "next/link"
import { getDatabaseEvidence } from "@/lib/operations/database"
import { sourceSignals } from "@/lib/operations/evidence-shared"

const time = (value: string | null) => value && Number.isFinite(Date.parse(value)) ? new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Not observed"
export default async function DatabaseEvidence() {
  const data = await getDatabaseEvidence()
  if (data.access !== "allowed" || !data.available) return <section id="sources" className="rounded-2xl border p-6"><h2 className="text-2xl font-bold">Source health & review</h2><p role="status" className="mt-3">Database evidence unavailable. Retry later; this does not establish empty supply.</p></section>
  const now = new Date()
  const groups = [data.discovery, data.deals, data.news]
  const sources = groups.flatMap(group => group.available ? group.value : [])
  sources.sort((a, b) => Number(sourceSignals(b, now).attention) - Number(sourceSignals(a, now).attention) || a.name.localeCompare(b.name))
  return <section id="sources" className="scroll-mt-24 space-y-5">
    <div><h2 className="text-2xl font-bold">Source health & review</h2><p className="mt-2 text-sm text-muted-foreground">Read {time(data.fetchedAt)} UK time. Counts cover the national registry; W3 radius and age suitability still require pilot review. A check within 36 hours is a freshness signal, not seven-day acceptance.</p></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{[
      ["Public venue records", data.venues], ["Current activity view", data.activities], ["Upcoming event view", data.events],
      ["Hidden venue records", data.hidden], ["Unwithdrawn listings without venue links", data.unmatched],
    ].map(([label, result]) => {
      const metric = result as typeof data.venues
      return <article key={String(label)} className="rounded-2xl border bg-card p-5"><h3 className="text-sm font-semibold">{String(label)}</h3><p className="mt-3 text-3xl font-bold">{metric.available ? metric.value.toLocaleString("en-GB") : "Unavailable"}</p></article>
    })}</div>
    <p className="text-sm text-muted-foreground">View counts precede public display filters. Hidden records include discovery candidates and other hidden venues; unresolved queues include historical listings. They are review backlogs, not accepted public supply.</p>
    <nav aria-label="Evidence review queues" className="flex flex-wrap gap-4 font-semibold"><Link href="/ops/review?kind=venues" className="underline underline-offset-4">Hidden venues</Link><Link href="/ops/review?kind=activities" className="underline underline-offset-4">Unresolved activities</Link><Link href="/ops/review?kind=events" className="underline underline-offset-4">Unresolved events</Link></nav>
    {groups.some(group => !group.available) && <p role="status" className="rounded-xl border p-4">Some source families are unavailable or incomplete. Available families remain below; missing families are not counted as zero.</p>}
    <div className="grid gap-4 md:grid-cols-2">{sources.map(source => {
      const signals = sourceSignals(source, now)
      return <article key={`${source.family}-${source.id}`} className="min-w-0 rounded-2xl border bg-card p-5">
        <h3 className="break-words font-bold">{source.name}</h3><p className="mt-1 text-sm text-muted-foreground">{source.family} · {source.role || "Feed"} · {[source.nation, source.region].filter(Boolean).join(" / ") || "Location not recorded"}</p>
        <p className={`mt-3 text-sm font-semibold ${signals.attention ? "text-amber-800 dark:text-amber-300" : ""}`}>{signals.collection} · {signals.freshness}</p>
        <dl className="mt-3 space-y-2 text-sm"><div><dt className="text-muted-foreground">Last check</dt><dd>{time(source.checked)}</dd></div><div><dt className="text-muted-foreground">Last successful fetch</dt><dd>{time(source.succeeded)}</dd></div><div><dt className="text-muted-foreground">Consecutive failures</dt><dd>{source.failures}</dd></div><div><dt className="text-muted-foreground">Latest reported yield</dt><dd>{signals.yield}</dd></div></dl>
      </article>
    })}</div>
    <p className="text-sm text-muted-foreground">Inactive sources still need suitability and access review. Zero observed yield can reflect no offers, extraction or quality filtering; it does not prove no local activities. Venue reference and news feeds may have no stored per-source yield/success timestamp. Failure details and raw payloads stay outside this view.</p>
  </section>
}

import Link from "next/link"
import { notFound, redirect } from "next/navigation"
import { getReviewQueue } from "@/lib/operations/database"
import { PAGE_SIZE, evidenceUrl } from "@/lib/operations/evidence-shared"
import { pageMetadata } from "@/lib/seo"

export const dynamic = "force-dynamic"
export const metadata = pageMetadata("Evidence review", "/ops/review", "Dadspace operator evidence review", { noIndex: true })
const labels = { venues: "Hidden venues", activities: "Unresolved activities", events: "Unresolved events" }
const time = (value: string | null) => value && Number.isFinite(Date.parse(value)) ? new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "Not observed"
function EvidenceLink({ value, label }: { value: string | null; label: string }) {
  const href = evidenceUrl(value)
  return href ? <a href={href} target="_blank" rel="noopener noreferrer" className="underline underline-offset-4">{label}</a> : <span className="text-muted-foreground">{label} unavailable</span>
}
export default async function ReviewPage({ searchParams }: { searchParams: Promise<{ kind?: string | string[]; page?: string | string[] }> }) {
  const params = await searchParams
  const data = await getReviewQueue(params.kind, params.page)
  if (data.access === "sign-in") redirect("/auth/login?next=%2Fops%2Freview")
  if (data.access === "denied") notFound()
  if (data.access !== "allowed") return <section className="rounded-2xl border p-6"><h1 className="text-3xl font-bold">Review unavailable</h1><p className="mt-3">Operator sign-in could not be verified. Retry later.</p></section>
  const href = (page: number) => `/ops/review?kind=${data.kind}&page=${page}`
  return <div className="space-y-6">
    <header><Link href="/ops#sources" className="text-sm font-semibold underline">Back to operations</Link><h1 className="mt-4 text-3xl font-bold">{labels[data.kind]}</h1><p className="mt-3 max-w-3xl text-muted-foreground">Read-only evidence, newest observations first. National backlog, including historical listings; no W3 distance or age acceptance is implied. Publication, classification and canonical matching need a reviewed decision.</p></header>
    <nav aria-label="Review queue types" className="flex flex-wrap gap-4">{Object.entries(labels).map(([kind, label]) => <Link key={kind} href={`/ops/review?kind=${kind}`} aria-current={kind === data.kind ? "page" : undefined} className="font-semibold underline underline-offset-4">{label}</Link>)}</nav>
    {!data.result.available ? <p role="status" className="rounded-xl border p-5">Queue evidence unavailable or incomplete. Retry later; this does not establish an empty queue.</p> : <>
      <p className="text-sm">{data.result.value.total.toLocaleString("en-GB")} records · Page {data.page} · Up to {PAGE_SIZE} per page</p>
      {data.result.value.rows.length === 0 && <p role="status" className="rounded-xl border p-5">{data.result.value.total === 0 ? "No records currently match this queue." : "This page is beyond the current queue. Choose the first page."}</p>}
      <div className="grid gap-5">{data.result.value.rows.map(row => <article key={row.id} className="min-w-0 rounded-2xl border bg-card p-6">
        <h2 className="break-words text-xl font-bold">{row.title}</h2><p className="mt-2 text-sm text-muted-foreground">{row.status || "Status unknown"} · {row.postcode || "Postcode missing"} · Observed {time(row.observed)} UK time</p>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2"><div><dt className="font-semibold">Location evidence</dt><dd className="break-words">{[row.venue, row.address].filter(Boolean).join(" · ") || "Not recorded"}</dd></div><div><dt className="font-semibold">Recorded source</dt><dd className="break-words">{row.source || "See source evidence"}</dd></div>
          {data.kind !== "venues" && <><div><dt className="font-semibold">Published dates</dt><dd>{row.start || "Not recorded"} → {row.end || "Not recorded"}</dd></div><div><dt className="font-semibold">Ages / recurrence evidence</dt><dd>{row.age || "Ages not recorded"} · {row.recurrence || "Recurrence not recorded"}</dd></div><div className="sm:col-span-2"><dt className="font-semibold">Stored schedule</dt><dd className="whitespace-pre-wrap break-words">{row.schedule || "Not recorded"}</dd></div></>}
        </dl><div className="mt-5 flex flex-wrap gap-5 text-sm font-semibold"><EvidenceLink value={row.sourceUrl} label="Source evidence"/><EvidenceLink value={row.detailUrl} label="Discovery / listing detail"/></div>
        {data.kind === "venues" && <Link className="mt-4 inline-block font-semibold underline" href={`/ops/decision?kind=${data.kind}&record=${row.id}`}>Review decision options</Link>}<p className="mt-4 break-all text-xs text-muted-foreground">Record: {row.id}</p>
      </article>)}</div>
      <nav aria-label="Review pagination" className="flex flex-wrap gap-5 font-semibold"><Link href={href(1)} className="underline">First page</Link>{data.page > 1 && <Link href={href(data.page - 1)} className="underline">Previous page</Link>}{data.page * PAGE_SIZE < data.result.value.total && <Link href={href(data.page + 1)} className="underline">Next page</Link>}</nav>
    </>}
  </div>
}

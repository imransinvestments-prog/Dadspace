import Link from "next/link"
import { redirect, notFound } from "next/navigation"
import { pageMetadata } from "@/lib/seo"
import { getDealsEvidence } from "@/lib/operations/deals-evidence"
import MaintenanceForm from "../editorial/maintenance-form"
import { maintenanceConfiguration } from "@/lib/operations/maintenance"

export const dynamic = "force-dynamic"
export const metadata = pageMetadata("Deals maintenance", "/ops/deals", "Deal coverage, evidence and merchant readiness", { noIndex: true })
const tabs = [{ id: "offers", name: "Offer evidence" }, { id: "taxonomy", name: "Canonical items & aliases" }, { id: "sources", name: "Sources & merchant readiness" }, { id: "audit", name: "Action history" }]
export default async function DealsOperationsPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams
  const kind = tabs.some(t => t.id === params.kind) ? String(params.kind) : "offers"
  const filters = kind === "taxonomy" ? ["all", "active", "inactive", "aliases"] : kind === "sources" ? ["all", "active", "inactive"] : kind === "audit" ? ["all"] : ["all", "live"]
  const filter = typeof params.filter === "string" && filters.includes(params.filter) ? params.filter : "all"
  const page = typeof params.page === "string" && /^[1-9]\d{0,3}$/.test(params.page) ? Number(params.page) : 1
  const { access, evidence } = await getDealsEvidence(kind, page, filter)
  if (access === "sign-in") redirect("/auth/login?next=%2Fops%2Fdeals")
  if (access === "denied") notFound()
  if (access !== "allowed") return <h1>Operator sign-in could not be verified.</h1>
  const config = maintenanceConfiguration()
  const seed = { family: "deals-source", action: ["pause", "activate", "restore"].includes(String(params.action)) ? String(params.action) : "pause", record: typeof params.record === "string" ? params.record.slice(0, 100) : "" }
  return <div className="space-y-8">
    <header><Link className="underline" href="/ops">Operations</Link><h1 className="mt-4 text-3xl font-bold">Deals evidence & maintenance</h1><p className="mt-3 max-w-3xl">Understand which offers are displayed, where coverage is missing and what each source actually supplied. Review access and permission to change records are separate.</p></header>
    <nav aria-label="Deals queues" className="flex flex-wrap gap-3">{tabs.map(t => <Link key={t.id} aria-current={kind === t.id ? "page" : undefined} href={`/ops/deals?kind=${t.id}`} className="rounded-lg border px-4 py-3 font-semibold">{t.name}</Link>)}</nav>
    <section className="rounded-2xl border p-5"><h2 className="text-xl font-bold">Priority family costs</h2><p className="mt-3">Holidays, school uniforms, car seats, bicycles and tuition are the five review priorities. At least three need current owner-approved offers. Missing supply stays visible; successful fetches and generic promotions do not satisfy that goal.</p><p className="mt-3 text-sm">Affiliate commission does not determine usefulness. Joined programmes, pending decisions and tracking delivery need separate evidence. The previous AWIN review is historical, not current membership confirmation.</p><a className="mt-3 inline-block underline" href="https://github.com/imransinvestments-prog/Dadspace/issues/131">Coverage findings and owner decisions · #131</a></section>
    <p className="rounded-xl border p-4">{config.live ? "Production maintenance is enabled for separately authorised maintainers." : "Live changes are disabled on this deployment."} A preview makes no change.</p>
    <section aria-label="Deals evidence" className="space-y-4">
      <nav aria-label="Queue filters" className="flex flex-wrap gap-4">{filters.map(f => <Link key={f} aria-current={filter === f ? "page" : undefined} className="underline" href={`/ops/deals?kind=${kind}&filter=${f}`}>{f}</Link>)}</nav>
      {!evidence.available ? <p role="status" className="rounded-xl border p-5">This queue is unavailable. A failed evidence request does not establish an empty feed.</p> : <>
        <p>{evidence.total} stored records · page {page}. Stored status is separate from public eligibility and owner acceptance.</p>
        {evidence.rows.length === 0 && <p className="rounded-xl border p-5">No records match this queue and page.</p>}
        {evidence.rows.map(row => <article key={row.id} className="min-w-0 space-y-3 rounded-2xl border bg-card p-5"><p className="text-sm text-muted-foreground">Record {row.id} · {row.source}</p><h2 className="text-xl font-bold">{row.title}</h2><p className="font-semibold">{row.state}</p>{row.date && <p className="text-sm">Last checked: {row.date}</p>}<p className="whitespace-pre-wrap break-words text-sm">{row.detail}</p>{row.url && <a className="block break-all underline" href={row.url} target="_blank" rel="noreferrer">Source evidence: {row.url}</a>}{kind === "sources" && <Link className="inline-block underline" href={`/ops/deals?kind=sources&action=${row.state === "Active" ? "pause" : "activate"}&record=${row.id}#maintenance`}>Prepare source decision</Link>}</article>)}
        <nav aria-label="Queue pages" className="flex gap-5">{page > 1 && <Link className="underline" href={`/ops/deals?kind=${kind}&filter=${filter}&page=${page - 1}`}>Previous</Link>}{page * 20 < (evidence.total ?? 0) && <Link className="underline" href={`/ops/deals?kind=${kind}&filter=${filter}&page=${page + 1}`}>Next</Link>}</nav>
      </>}
    </section>
    {["sources", "audit"].includes(kind) && <div id="maintenance" className="scroll-mt-24"><MaintenanceForm key={JSON.stringify(seed)} initial={seed} dealsOnly /></div>}
    <p className="text-sm text-muted-foreground">Source decisions reuse the shared signed preview and audit controls. A preview makes no change. Taxonomy edits and paid retries are not enabled here. Existing accepted reviews remain in the <Link className="underline" href="/ops/reviews">review desk</Link>.</p>
  </div>
}

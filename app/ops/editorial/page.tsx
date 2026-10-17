import Link from "next/link"
import { redirect, notFound } from "next/navigation"
import { pageMetadata } from "@/lib/seo"
import { getEditorialEvidence } from "@/lib/operations/editorial"
import { maintenanceConfiguration } from "@/lib/operations/maintenance"
import { publicEvidenceUrl } from "@/lib/operations/review-edit"
import MaintenanceForm from "./maintenance-form"

export const dynamic = "force-dynamic"
export const metadata = pageMetadata("Editorial maintenance", "/ops/editorial", "News and Originals upkeep", { noIndex: true })
const tabs = [{ id: "news", name: "News articles" }, { id: "originals", name: "Published Originals" }, { id: "drafts", name: "Drafts & generation" }, { id: "sources", name: "News sources" }, { id: "audit", name: "Action history" }]
export default async function EditorialPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await searchParams
  const kind = tabs.some(t => t.id === params.kind) ? String(params.kind) : "originals"
  const filters = kind === "news" ? ["all", "hidden", "duplicates", "low-relevance", "missing-link"] : kind === "drafts" ? ["all", "rejected", "failed"] : kind === "originals" ? ["all", "hidden"] : ["all"]
  const filter = typeof params.filter === "string" && filters.includes(params.filter) ? params.filter : "all"
  const page = typeof params.page === "string" && /^[1-9]\d{0,3}$/.test(params.page) ? Number(params.page) : 1
  const { access, evidence } = await getEditorialEvidence(kind, page, filter)
  if (access === "sign-in") redirect("/auth/login?next=%2Fops%2Feditorial")
  if (access === "denied") notFound()
  if (access !== "allowed") return <h1>Operator sign-in could not be verified.</h1>
  const config = maintenanceConfiguration()
  const seed = { family: ["news", "originals", "news-source", "deals-source", "discovery-source"].includes(String(params.family)) ? String(params.family) : "news", action: ["hide", "pause", "activate", "restore", "retry", "reconcile"].includes(String(params.action)) ? String(params.action) : "hide", record: typeof params.record === "string" ? params.record.slice(0, 100) : "" }
  return <div className="space-y-8"><header><Link className="underline" href="/ops">Operations</Link><h1 className="mt-4 text-3xl font-bold">News & Originals maintenance</h1><p className="mt-3">Inspect article evidence, future retained drafts and failed generation. Review access does not grant maintenance permission.</p>
    <p className="mt-3 rounded-xl border p-4">{config.live ? "Production maintenance enabled for separately authorised maintainers." : "Live actions are disabled on this deployment."} Signing configuration: {config.signing ? "present" : "missing"}; runner configuration: {config.dispatch ? "present" : "missing"}. Secret values are never displayed.</p></header>
    <nav aria-label="Editorial queues" className="flex flex-wrap gap-3">{tabs.map(t => <Link key={t.id} aria-current={kind === t.id ? "page" : undefined} href={`/ops/editorial?kind=${t.id}`} className={`rounded-lg border px-4 py-3 ${kind === t.id ? "bg-primary text-primary-foreground" : ""}`}>{t.name}</Link>)}</nav>
    <section aria-label="Queue evidence" className="space-y-4">
      {filters.length > 1 && <nav aria-label="Queue filters" className="flex flex-wrap gap-4">{filters.map(f => <Link key={f} aria-current={filter === f ? "page" : undefined} className="underline" href={`/ops/editorial?kind=${kind}&filter=${f}`}>{f.replaceAll("-", " ")}</Link>)}</nav>}
      {!evidence.available ? <p className="rounded-xl border p-5">This queue is unavailable. The reviewed database schema or service connection may not yet be installed. This is not evidence of an empty queue.</p> : <>
        <p>{evidence.total} stored records · page {page}. Stored articles are not automatically eligible public content.</p>
        {!evidence.rows.length && <p>No records in this page. Historical drafts were not retained; an empty draft queue does not prove that no failures occurred.</p>}
        {evidence.rows.map(row => <article key={row.id} className="rounded-2xl border bg-card p-5"><p className="text-sm font-semibold">{row.state}</p><h2 className="mt-2 text-xl font-bold">{row.title}</h2><p className="mt-2 break-all text-sm">ID: {row.id}</p><p className="mt-2 text-sm">{row.source || "Source unknown"} · {row.date ? new Date(row.date).toLocaleString("en-GB", { timeZone: "Europe/London" }) : "Date unknown"}</p>{row.url && publicEvidenceUrl(row.url) && <a className="mt-3 inline-block break-all underline" href={row.url} target="_blank" rel="noopener noreferrer">{row.url}</a>}{row.detail && <p className="mt-3 text-sm">{row.detail}</p>}{row.draft && <details className="mt-4"><summary className="cursor-pointer font-semibold">Read article / draft evidence</summary><p className="mt-3 whitespace-pre-wrap">{row.draft}</p></details>}</article>)}
        <nav aria-label="Queue pages" className="flex gap-5">{page > 1 && <Link className="underline" href={`/ops/editorial?kind=${kind}&filter=${filter}&page=${page - 1}`}>Previous page</Link>}{page * 20 < (evidence.total || 0) && <Link className="underline" href={`/ops/editorial?kind=${kind}&filter=${filter}&page=${page + 1}`}>Next page</Link>}</nav>
      </>}
    </section>
    {evidence.available && ["news", "originals", "sources"].includes(kind) && <section className="rounded-xl border p-5"><h2 className="font-bold">Choose a record to preview</h2><div className="mt-3 flex flex-wrap gap-3">{evidence.rows.map(row => <Link key={row.id} href={`/ops/editorial?kind=${kind}&filter=${filter}&page=${page}&family=${kind === "sources" ? "news-source" : kind}&action=${kind === "sources" ? row.state === "Active" ? "pause" : "activate" : "hide"}&record=${encodeURIComponent(row.id)}#maintenance`} className="rounded-lg border px-3 py-2 text-sm">{kind === "sources" ? "Source decision" : "Unpublish preview"}: {row.title}</Link>)}</div></section>}
    <div id="maintenance" className="scroll-mt-24"><MaintenanceForm key={JSON.stringify(seed)} initial={seed} /></div>
    <p className="text-sm text-muted-foreground">Existing content approvals remain recorded in the <Link className="underline" href="/ops/reviews">review desk</Link>. A submitted workflow is not a successful collection or publication; follow its action history and actual public readback. Cross-feed seven-day acceptance remains in #125.</p>
  </div>
}

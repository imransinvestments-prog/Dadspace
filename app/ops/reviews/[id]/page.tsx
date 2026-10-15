import Link from "next/link"
import { notFound, redirect } from "next/navigation"
import { operationsAccess } from "@/lib/operations/session"
import { reviewTask } from "@/lib/operations/review-tasks"
import { getTaskReview, reviewReadiness } from "@/lib/operations/task-review"
import { getReviewMaterial, materialFingerprint, materialPage, MATERIAL_PAGE_SIZE } from "@/lib/operations/review-material"
import { evidenceUrl } from "@/lib/operations/evidence-shared"
import { pageMetadata } from "@/lib/seo"
import DatabaseEvidence from "../../database-evidence"
import ReviewForm from "../review-form"
export const dynamic = "force-dynamic"
export const metadata = pageMetadata("Task review", "/ops/reviews", "Protected owner review", { noIndex: true })

function Value({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === "") return <span className="text-muted-foreground">Not recorded</span>
  if (Array.isArray(value)) return value.length ? <ul className="space-y-3">{value.map((entry, index) => <li key={index}><Value value={entry}/></li>)}</ul> : <span>None recorded</span>
  if (typeof value === "object") return <dl className="space-y-2 border-l pl-3">{Object.entries(value).map(([key, entry]) => <div key={key}><dt className="text-sm font-semibold capitalize">{key.replaceAll("_", " ")}</dt><dd className="whitespace-pre-wrap break-words text-sm"><Value value={entry}/></dd></div>)}</dl>
  if (typeof value === "string" && /^https?:\/\//.test(value)) {
    const href = evidenceUrl(value)
    return href ? <a className="break-all underline" href={href} target="_blank" rel="noopener noreferrer">{href}</a> : <span>Source link unavailable</span>
  }
  return <span className="whitespace-pre-wrap break-words">{String(value)}</span>
}
export default async function TaskReviewPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ page?: string }> }) {
  const access = await operationsAccess()
  if (access === "sign-in") redirect("/auth/login?next=%2Fops%2Freviews")
  if (access === "denied") notFound()
  if (access !== "allowed") return <p role="status">Review access could not be verified.</p>
  const task = reviewTask(Number((await params).id))
  if (!task) notFound()
  const page = materialPage((await searchParams).page)
  const [taskResult, materialResult, readinessResult] = await Promise.allSettled([getTaskReview(task.id), getReviewMaterial(task.id, page), reviewReadiness()])
  const data = taskResult.status === "fulfilled" ? taskResult.value : null
  const material = materialResult.status === "fulfilled" ? materialResult.value : null
  const readiness = readinessResult.status === "fulfilled" ? readinessResult.value : { canSave: false, reasons: ["Reviewer identity could not be verified. Retry after signing in again."] }
  const reasons = [...readiness.reasons]
  if (!data) reasons.push("GitHub task/history is unavailable. Check that the token is valid for Dadspace; retry or inspect the GitHub task.")
  if (data && data.issue.state !== "open") reasons.push("This GitHub task is closed; review its history before making further decisions.")
  const disabledReason = reasons.join(" ") || undefined
  const version = data ? `${data.issue.updated_at}:${data.history.at(-1)?.id || 0}` : ""
  const body = data?.issue.body.split("<!-- /dadspace-weekly-planning -->").at(-1)?.split("<details>")[0]
  return <div className="space-y-6">
    <header><div className="flex flex-wrap gap-4"><Link href="/ops/reviews" className="underline">All reviews</Link><Link href="/ops" className="underline">Operations page</Link><a href={`https://github.com/imransinvestments-prog/Dadspace/issues/${task.id}`} className="underline">GitHub task #{task.id}</a></div><h1 className="mt-4 text-3xl font-bold">{task.title}</h1><p className="mt-3">{task.need}</p><nav aria-label="Review sections" className="mt-4 flex flex-wrap gap-4 font-semibold"><a className="underline" href="#review-data">Review actual data</a><a className="underline" href="#overall-decision">Overall decision</a><a className="underline" href="#review-history">Decision history</a></nav></header>
    <section className="rounded-2xl border bg-card p-5" aria-label="Review saving status"><h2 className="font-bold">{disabledReason ? "Review form setup needs attention" : "Ready to save review decisions"}</h2>{reasons.length ? <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul> : <p className="mt-2 text-sm">Your reviewer identity and a GitHub credential are configured. Saving will check the task and record again.</p>}<p className="mt-2 text-sm text-muted-foreground">Decision forms remain visible below. Setup issues disable saving, without hiding the controls.</p></section>
    <section id="review-data" className="space-y-5 scroll-mt-24"><h2 className="text-2xl font-bold">{material?.label || "Review data"}</h2><p className="text-sm text-muted-foreground">{material?.notice || "Review data could not be loaded. Retry later; this does not establish an empty queue."}</p>
      {material?.available && <><p className="text-sm">{material.total} records · Page {page} · Up to {MATERIAL_PAGE_SIZE} per page</p>{!material.rows.length && <p role="status">{material.total ? "No records on this page. Return to page one." : "No records currently match this dataset. A missing sample is not acceptance."}</p>}
        {material.rows.map(row => <article key={row.id} className="min-w-0 space-y-5 rounded-2xl border bg-card p-5 sm:p-6"><div><p className="break-all text-xs text-muted-foreground">Record {row.id}</p><h3 className="mt-2 text-xl font-bold">{row.title}</h3></div><Value value={row.fields}/><ReviewForm key={`${row.id}:${version}`} id={task.id} version={version} disabledReason={disabledReason} record={{ rowId: row.id, fingerprint: materialFingerprint(row), page }}/></article>)}
        <nav aria-label="Review data pages" className="flex flex-wrap gap-5 font-semibold"><Link className="underline" href={`/ops/reviews/${task.id}?page=1#review-data`}>First page</Link>{page > 1 && <Link className="underline" href={`/ops/reviews/${task.id}?page=${page - 1}#review-data`}>Previous page</Link>}{page * MATERIAL_PAGE_SIZE < material.total && <Link className="underline" href={`/ops/reviews/${task.id}?page=${page + 1}#review-data`}>Next page</Link>}</nav></>}
    </section>
    {task.id === 149 && <section className="space-y-5"><h2 className="text-2xl font-bold">Live operational evidence</h2><DatabaseEvidence/></section>}
    <section id="overall-decision" className="scroll-mt-24"><ReviewForm key={version} id={task.id} version={version} disabledReason={disabledReason}/></section>
    <details className="rounded-2xl border p-5"><summary className="cursor-pointer font-bold">Task acceptance criteria and delivery context</summary>{body ? <pre className="mt-4 whitespace-pre-wrap break-words font-sans text-sm">{body}</pre> : <p className="mt-3">Task text unavailable. Open the GitHub task for current criteria.</p>}</details>
    <section id="review-history" className="scroll-mt-24"><h2 className="text-xl font-bold">Decision history</h2><p className="mt-2 text-sm text-muted-foreground">GitHub author and recorded scope are retained. Comments are not automatically verified owner acceptance.</p>{!data ? <p>History unavailable. Check GitHub before retrying a save.</p> : !data.history.length ? <p className="mt-3">No review-desk decisions recorded.</p> : <div className="mt-4 space-y-4">{[...data.history].reverse().map(comment => <details key={comment.id} className="rounded-xl border p-5"><summary className="cursor-pointer font-semibold">{comment.user.login} · {comment.created_at}</summary><pre className="mt-3 whitespace-pre-wrap break-words font-sans text-sm">{comment.body}</pre><a href={comment.html_url} className="mt-3 inline-block underline">View recorded decision</a></details>)}</div>}</section>
  </div>
}

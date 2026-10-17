import Link from "next/link"
import { notFound, redirect } from "next/navigation"
import { operationsAccess } from "@/lib/operations/session"
import { reviewTask } from "@/lib/operations/review-tasks"
import { getTaskReview, reviewReadiness } from "@/lib/operations/task-review"
import { getReviewMaterial, materialFingerprint, materialPage, MATERIAL_PAGE_SIZE } from "@/lib/operations/review-material"
import { evidenceUrl } from "@/lib/operations/evidence-shared"
import { NEWS_SAMPLE, newsProgress, newsGeography } from "@/lib/operations/news-sample"
import { dealProgress } from "@/lib/operations/deal-checks"
import { previousOriginalsChecks, originalBodyWords } from "@/lib/operations/originals-checks"
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
  const progress = task.id === 126 && data ? newsProgress(data.history) : null
  const deals = task.id === 130 && data ? dealProgress(data.history) : null
  const nextIndex = progress ? NEWS_SAMPLE.rows.findIndex(row => !progress.reviews[row.id]) : -1
  const nextReview = nextIndex >= 0 ? `/ops/reviews/126?page=${Math.floor(nextIndex / MATERIAL_PAGE_SIZE) + 1}#record-${NEWS_SAMPLE.rows[nextIndex].id}` : null
  return <div className="space-y-6">
    <header><div className="flex flex-wrap gap-4"><Link href="/ops/reviews" className="underline">All reviews</Link><Link href="/ops" className="underline">Operations page</Link><a href={`https://github.com/imransinvestments-prog/Dadspace/issues/${task.id}`} className="underline">GitHub task #{task.id}</a></div><h1 className="mt-4 text-3xl font-bold">{task.title}</h1><p className="mt-3">{task.need}</p><nav aria-label="Review sections" className="mt-4 flex flex-wrap gap-4 font-semibold"><a className="underline" href="#review-data">Review actual data</a><a className="underline" href="#overall-decision">Overall decision</a><a className="underline" href="#review-history">Decision history</a></nav></header>
    <section className="rounded-2xl border bg-card p-5" aria-label="Review saving status"><h2 className="font-bold">{disabledReason ? "Review form setup needs attention" : "Ready to save review decisions"}</h2>{reasons.length ? <ul className="mt-3 list-disc space-y-2 pl-5 text-sm">{reasons.map(reason => <li key={reason}>{reason}</li>)}</ul> : <p className="mt-2 text-sm">Your reviewer identity and a GitHub credential are configured. Saving will check the task and record again.</p>}<p className="mt-2 text-sm text-muted-foreground">Decision forms remain visible below. Setup issues disable saving, without hiding the controls.</p></section>
    {task.id === 126 && <section aria-label="News sample progress" className="space-y-3 rounded-2xl border bg-card p-6"><h2 className="text-2xl font-bold">{progress ? `${progress.reviewed} of 50 articles reviewed` : "Review progress unavailable"}</h2>{progress && <><progress value={progress.reviewed} max={50} aria-label="Articles with a saved decision" className="h-3 w-full"/><p>{progress.remaining ? `${progress.remaining} remaining. Each article counts once, even if you update its decision.` : "All 50 have saved decisions. Check the scored criteria and outstanding issues before overall acceptance."}</p><dl className="grid gap-3 text-sm sm:grid-cols-2"><div><dt className="font-semibold">Relevant and correctly attributed</dt><dd>{progress.relevantAndAttributed}/50 confirmed · target 45/50</dd><dd>Relevance checked: {progress.relevanceChecked}/50; attribution checked: {progress.attributionChecked}/50</dd></div><div><dt className="font-semibold">Working article destinations</dt><dd>{progress.linksWorking}/50 confirmed · target 48/50</dd><dd>Links checked: {progress.linksChecked}/50</dd></div><div><dt className="font-semibold">Geographic targeting</dt><dd>{progress.geographyCorrect}/50 confirmed appropriate · {progress.geographyChecked}/50 checked</dd></div><div><dt className="font-semibold">Summary / date / sensitive-label / homepage checks</dt><dd>Summaries: {progress.summariesAccepted}/50 · Dates: {progress.datesAccepted}/50</dd><dd>Sensitive handling: {progress.sensitiveLabelsAccepted}/50 · Homepage presentation: {progress.homepagePicksAccepted}/50</dd></div></dl><p className="text-sm text-muted-foreground">Previous approvals count toward saved decisions. Missing individual checks remain unconfirmed. Approving relevance alone does not certify attribution, links or geography.</p>{nextReview && <Link href={nextReview} className="inline-flex rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground">Continue with next unreviewed article</Link>}</>}<details><summary className="cursor-pointer text-sm font-semibold">How these 50 were selected</summary><p className="mt-2 text-sm">{NEWS_SAMPLE.method}</p><p className="mt-2 text-sm">Sample {NEWS_SAMPLE.id}. Frozen snapshots keep the same articles and order when the live feed changes.</p></details></section>}
    {deals && <section className="space-y-3 rounded-2xl border bg-card p-6"><h2 className="text-2xl font-bold">Deals review: {deals.checked}/{deals.denominator} with saved checks</h2><p>All six checks passed: {deals.allChecksPassed}/{deals.denominator}. Known failures: {deals.knownFailures}. The same records supply the top-offer review ({deals.topDenominator} available); do not review them twice.</p><p className="text-sm text-muted-foreground">Proposed smaller-pool threshold: at least {Math.ceil(deals.denominator * 0.9)}/{deals.denominator} useful, accurate and actionable, with zero known expired/unavailable offers or unsupported savings. Owner agreement and changed-fact readback are required before acceptance. A saved review does not publish or hide an offer.</p></section>}
    <section id="review-data" className="space-y-5 scroll-mt-24"><h2 className="text-2xl font-bold">{material?.label || "Review data"}</h2><p className="text-sm text-muted-foreground">{material?.notice || "Review data could not be loaded. Retry later; this does not establish an empty queue."}</p>
      {material?.available && <><p className="text-sm">{material.total} records · Page {page} · Up to {MATERIAL_PAGE_SIZE} per page</p>{!material.rows.length && <p role="status">{material.total ? "No records on this page. Return to page one." : "No records currently match this dataset. A missing sample is not acceptance."}</p>}
        {material.rows.map(row => {
          const reviewed = progress?.reviews[row.id]
          const geo = task.id === 126 ? newsGeography(row.fields) : null
          const editorial = task.id === 128 && data ? previousOriginalsChecks(data.history, row.id, materialFingerprint(row)) : undefined
          return <article id={`record-${row.id}`} key={row.id} className="min-w-0 scroll-mt-24 space-y-5 rounded-2xl border bg-card p-5 sm:p-6"><div><p className="break-all text-xs text-muted-foreground">Record {row.id}{task.id === 126 ? ` · Article ${(page - 1) * MATERIAL_PAGE_SIZE + material.rows.indexOf(row) + 1} of 50` : ""}</p><h3 className="mt-2 text-xl font-bold">{row.title}</h3>{task.id === 126 && <p className="mt-2 font-semibold">{reviewed ? `Reviewed: ${reviewed.decision}` : "Awaiting your review"}</p>}</div>
            <details open={!reviewed}><summary className="cursor-pointer font-semibold">{reviewed ? "View article or update your review" : "Article and decision form"}</summary><div className="mt-4 space-y-5">{geo && <aside className="space-y-2 rounded-xl border bg-muted p-4"><h4 className="font-bold">Geographic relevance</h4><p className="text-sm">Stored scope: {geo.scope} · {geo.area}</p><p>{geo.guidance}</p><p className="text-sm text-muted-foreground">{geo.limitation}</p></aside>}{task.id === 128 && <p className="rounded-xl border bg-muted p-4 font-semibold">{row.fields.cadence === "weekly" ? "Weekly guide" : "Daily article"} · {originalBodyWords(row.fields) ?? "Unknown"} body words (section headings and paragraphs)</p>}<Value value={row.fields}/><ReviewForm key={`${row.id}:${version}`} id={task.id} version={version} disabledReason={disabledReason} previousChecks={task.id === 128 ? editorial : task.id === 130 ? deals?.reviews[row.id]?.checks : reviewed?.checks} record={{ rowId: row.id, fingerprint: materialFingerprint(row), page }}/></div></details></article>
        })}
        <nav aria-label="Review data pages" className="flex flex-wrap gap-5 font-semibold"><Link className="underline" href={`/ops/reviews/${task.id}?page=1#review-data`}>First page</Link>{page > 1 && <Link className="underline" href={`/ops/reviews/${task.id}?page=${page - 1}#review-data`}>Previous page</Link>}{page * MATERIAL_PAGE_SIZE < material.total && <Link className="underline" href={`/ops/reviews/${task.id}?page=${page + 1}#review-data`}>Next page</Link>}</nav></>}
    </section>
    {task.id === 149 && <section className="space-y-5"><h2 className="text-2xl font-bold">Live operational evidence</h2><DatabaseEvidence/></section>}
    <section id="overall-decision" className="scroll-mt-24"><ReviewForm key={version} id={task.id} version={version} disabledReason={disabledReason}/></section>
    <details className="rounded-2xl border p-5"><summary className="cursor-pointer font-bold">Task acceptance criteria and delivery context</summary>{body ? <pre className="mt-4 whitespace-pre-wrap break-words font-sans text-sm">{body}</pre> : <p className="mt-3">Task text unavailable. Open the GitHub task for current criteria.</p>}</details>
    <section id="review-history" className="scroll-mt-24"><h2 className="text-xl font-bold">Decision history</h2><p className="mt-2 text-sm text-muted-foreground">GitHub author and recorded scope are retained. Comments are not automatically verified owner acceptance.</p>{!data ? <p>History unavailable. Check GitHub before retrying a save.</p> : !data.history.length ? <p className="mt-3">No review-desk decisions recorded.</p> : <div className="mt-4 space-y-4">{[...data.history].reverse().map(comment => <details key={comment.id} className="rounded-xl border p-5"><summary className="cursor-pointer font-semibold">{comment.user.login} · {comment.created_at}</summary><pre className="mt-3 whitespace-pre-wrap break-words font-sans text-sm">{comment.body}</pre><a href={comment.html_url} className="mt-3 inline-block underline">View recorded decision</a></details>)}</div>}</section>
  </div>
}

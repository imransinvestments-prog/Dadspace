import Link from "next/link"
import { notFound, redirect } from "next/navigation"
import { operationsAccess } from "@/lib/operations/session"
import { reviewTask } from "@/lib/operations/review-tasks"
import { getTaskReview, reviewWriteAccess } from "@/lib/operations/task-review"
import { pageMetadata } from "@/lib/seo"
import ReviewForm from "../review-form"
export const dynamic = "force-dynamic"
export const metadata = pageMetadata("Task review", "/ops/reviews", "Protected owner review", { noIndex: true })
export default async function TaskReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const access = await operationsAccess()
  if (access === "sign-in") redirect("/auth/login?next=%2Fops%2Freviews")
  if (access === "denied") notFound()
  if (access !== "allowed") return <p role="status">Review access could not be verified.</p>
  const task = reviewTask(Number((await params).id))
  if (!task) notFound()
  let data
  try { data = await getTaskReview(task.id) } catch { return <section><h1 className="text-2xl font-bold">Review evidence unavailable</h1><p className="mt-3">GitHub could not provide the complete current task and history. Retry later or review the task directly.</p><a className="underline" href={`https://github.com/imransinvestments-prog/Dadspace/issues/${task.id}`}>Open GitHub task #{task.id}</a><p><Link href="/ops/reviews" className="underline">Back to reviews</Link></p></section> }
  const canWrite = await reviewWriteAccess() && !!process.env.DADSPACE_REVIEW_GITHUB_TOKEN
  const version = `${data.issue.updated_at}:${data.history.at(-1)?.id || 0}`
  const body = data.issue.body.split("<!-- /dadspace-weekly-planning -->").at(-1)?.split("<details>")[0] || data.issue.body
  return <div className="space-y-6"><header><div className="flex flex-wrap gap-4"><Link href="/ops/reviews" className="underline">All reviews</Link><Link href="/ops" className="underline">Operations page</Link><Link href={task.route} className="underline">Inspect related evidence</Link><a href={`https://github.com/imransinvestments-prog/Dadspace/issues/${task.id}`} className="underline">GitHub task</a></div><h1 className="mt-4 text-3xl font-bold">{data.issue.title}</h1><p className="mt-3">GitHub task: {data.issue.state}. Evidence fetched on this page load. Dependencies and samples must be checked before acceptance.</p></header>
    <section className="rounded-2xl border p-6"><h2 className="text-xl font-bold">Current task and acceptance criteria</h2><p className="mt-2 text-sm text-muted-foreground">Task text is shown verbatim. Open GitHub for formatted links, attachments and all discussion.</p><pre className="mt-4 whitespace-pre-wrap break-words font-sans text-sm">{body}</pre></section>
    <section><h2 className="text-xl font-bold">Review history</h2><p className="mt-2 text-sm text-muted-foreground">Matching GitHub comments, with their GitHub author. These are recorded decisions, not automatic acceptance or verification of the commenter’s authority.</p>{!data.history.length && <p className="mt-3">No review-desk decisions recorded.</p>}<div className="mt-4 space-y-4">{data.history.map(comment => <article key={comment.id} className="rounded-xl border p-5"><p className="text-sm">{comment.user.login} · {comment.created_at}</p><pre className="mt-3 whitespace-pre-wrap break-words font-sans text-sm">{comment.body}</pre><a href={comment.html_url} className="mt-3 inline-block underline">View recorded decision</a></article>)}</div></section>
    {canWrite && data.issue.state === "open" ? <ReviewForm id={task.id} version={version}/> : <p role="status" className="rounded-xl border p-5">{data.issue.state !== "open" ? "This task is closed. Review its history on GitHub." : "Saving requires an explicitly configured reviewer identity and server-side GitHub credential. Read-only operations access does not grant review writes."}</p>}
  </div>
}

import Link from "next/link"
import { notFound, redirect } from "next/navigation"
import { operationsAccess } from "@/lib/operations/session"
import { REVIEW_TASKS } from "@/lib/operations/review-tasks"
import { pageMetadata } from "@/lib/seo"
export const dynamic = "force-dynamic"
export const metadata = pageMetadata("Human reviews", "/ops/reviews", "Dadspace owner review queue", { noIndex: true })
export default async function ReviewsPage() {
  const access = await operationsAccess()
  if (access === "sign-in") redirect("/auth/login?next=%2Fops%2Freviews")
  if (access === "denied") notFound()
  if (access !== "allowed") return <p role="status">Review access could not be verified. Retry later.</p>
  return <div className="space-y-6"><header><Link href="/ops" className="underline">Operations</Link><h1 className="mt-4 text-3xl font-bold">Your review desk</h1><p className="mt-3 max-w-3xl text-muted-foreground">Open a review to inspect actual records, source evidence and a decision form beside each item. Content views show live records; historical proposals and provider source samples show dated saved evidence. Samples and unfinished implementation still need checking before overall acceptance.</p></header>
    <div className="grid gap-5 md:grid-cols-2">{REVIEW_TASKS.map(task => <article key={task.id} className="rounded-2xl border bg-card p-6"><p className="text-sm text-muted-foreground">#{task.id} · Owner: Imran</p><h2 className="mt-2 text-xl font-bold">{task.title}</h2><p className="mt-3">{task.need}</p><p className="mt-3 text-sm">{task.dependencies.length ? `Prerequisites to check: ${task.dependencies.map(id => `#${id}`).join(", ")}` : "Check the live task for remaining evidence."}</p><div className="mt-5 flex flex-wrap gap-4 font-semibold"><Link href={`/ops/reviews/${task.id}`} className="underline">Review and update</Link><Link href="/ops" className="underline">Operations page</Link><a href={`https://github.com/imransinvestments-prog/Dadspace/issues/${task.id}`} className="underline">GitHub task</a></div></article>)}</div>
  </div>
}

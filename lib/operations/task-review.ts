import "server-only"
import { operationsAccess } from "./session"
import { createClient } from "@/lib/supabase/server"
import { isOperationsUser, isVerifiedOperationsEmail } from "./access"
import { REVIEW_DECISIONS, reviewTask } from "./review-tasks"

const API = "https://api.github.com/repos/imransinvestments-prog/Dadspace"
const MARKER = "Dadspace owner review v1"
export async function reviewWriteAccess() {
  if (await operationsAccess() !== "allowed") return false
  const { data, error } = await (await createClient()).auth.getUser()
  return !error && !!data.user && !data.user.is_anonymous && (
    isOperationsUser(data.user.id, process.env.DADSPACE_REVIEWER_USER_IDS) ||
    isVerifiedOperationsEmail(data.user, process.env.DADSPACE_REVIEWER_EMAILS))
}
async function github(path: string, body?: string) {
  const token = process.env.DADSPACE_REVIEW_GITHUB_TOKEN
  if (body && !token) throw new Error("Review saving is not configured")
  const response = await fetch(`${API}${path}`, {
    method: body ? "POST" : "GET", cache: "no-store", redirect: "error",
    signal: AbortSignal.timeout(15000),
    headers: { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
      ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(body ? { "Content-Type": "application/json" } : {}) }, body,
  })
  if (!response.ok) throw new Error("GitHub review request failed")
  return response.json()
}
type Comment = { id: number; body: string; html_url: string; created_at: string; user: { login: string } }
export async function getTaskReview(id: number) {
  if (!reviewTask(id) || await operationsAccess() !== "allowed") throw new Error("Review access denied")
  const issue = await github(`/issues/${id}`) as { title: string; body: string; state: string; updated_at: string }
  const history: Comment[] = []
  // Fetch every page, or fail explicitly rather than silently omitting decisions.
  for (let page = 1; page <= 20; page++) {
    const comments = await github(`/issues/${id}/comments?per_page=100&page=${page}`) as Comment[]
    history.push(...comments.filter(comment => comment.body.startsWith(`${MARKER}\n`)))
    if (comments.length < 100) return { issue, history }
  }
  throw new Error("Review history is too large; inspect the GitHub task")
}
export async function recordTaskReview(id: number, decision: string, notes: string, evidence: string, version: string) {
  if (!reviewTask(id) || !(REVIEW_DECISIONS as readonly string[]).includes(decision) || !notes.trim() || notes.length > 6000 || evidence.length > 2000) throw new Error("Invalid review")
  if (!await reviewWriteAccess()) throw new Error("Reviewer access required")
  const current = await getTaskReview(id)
  const latest = current.history.at(-1)?.id || 0
  if (`${current.issue.updated_at}:${latest}` !== version || current.issue.state !== "open") throw new Error("Review changed; reload before saving")
  const { data, error } = await (await createClient()).auth.getUser()
  if (error || !data.user) throw new Error("Sign in required")
  const saved = await github(`/issues/${id}/comments`, JSON.stringify({ body: `${MARKER}\n\nDecision: ${decision}\nReviewer (verified Dadspace user): ${data.user.id}\nReviewed issue version: ${version}\n\nScope / reason / follow-up:\n${notes.trim()}\n\nEvidence / sample IDs:\n${evidence.trim() || "Not supplied"}\n\nRecorded through /ops/reviews/${id}. This records a human decision only; outstanding acceptance, data application and release gates remain open.` })) as Comment
  return saved.id
}

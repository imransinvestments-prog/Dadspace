import "server-only"
import { operationsAccess } from "./session"
import { createClient } from "@/lib/supabase/server"
import { isOperationsUser, isVerifiedOperationsEmail } from "./access"
import { REVIEW_DECISIONS, reviewTask } from "./review-tasks"
import { validNewsChecks, type NewsChecks } from "./news-sample"
import { validOriginalsChecks, type OriginalsChecks } from "./originals-checks"

const API = "https://api.github.com/repos/imransinvestments-prog/Dadspace"
const MARKER = "Dadspace owner review v1"
export async function reviewReadiness() {
  if (await operationsAccess() !== "allowed") return { canSave: false, reasons: ["Operator sign-in could not be verified."] }
  const reasons: string[] = []
  if (!process.env.DADSPACE_REVIEW_GITHUB_TOKEN?.trim()) reasons.push("Missing DADSPACE_REVIEW_GITHUB_TOKEN on this deployment. Add the repository Issues read/write token in Vercel, then redeploy.")
  if (!process.env.DADSPACE_REVIEWER_USER_IDS?.trim() && !process.env.DADSPACE_REVIEWER_EMAILS?.trim()) reasons.push("Reviewer access is not configured. Set DADSPACE_REVIEWER_EMAILS to your verified Dadspace login email (or configure reviewer user IDs), then redeploy.")
  else if (!await reviewWriteAccess()) reasons.push("Your signed-in account does not match the configured reviewer identities. Check DADSPACE_REVIEWER_EMAILS and confirm your Dadspace email.")
  return { canSave: reasons.length === 0, reasons }
}
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
export async function recordTaskReview(id: number, decision: string, notes: string, evidence: string, version: string, material?: { rowId: string; fingerprint: string; page: number; checks?: NewsChecks; editorialChecks?: OriginalsChecks }) {
  if (!reviewTask(id) || !(REVIEW_DECISIONS as readonly string[]).includes(decision) || !notes.trim() || notes.length > 6000 || evidence.length > 2000) throw new Error("Invalid review")
  if (!await reviewWriteAccess()) throw new Error("Reviewer access required")
  if (material?.checks && (id !== 126 || !validNewsChecks(material.checks))) throw new Error("Invalid news quality checks")
  if (material?.editorialChecks && (id !== 128 || !validOriginalsChecks(material.editorialChecks))) throw new Error("Invalid Originals editorial checks")
  let snapshot = ""
  if (material) {
    const { getReviewMaterial, materialFingerprint } = await import("./review-material")
    const currentMaterial = await getReviewMaterial(id, material.page)
    const row = currentMaterial.rows.find(row => row.id === material.rowId)
    if (!currentMaterial.available || !row || materialFingerprint(row) !== material.fingerprint) throw new Error("Record evidence changed; reload before saving")
    snapshot = `\n\nReviewed record: ${row.id}\nSnapshot SHA-256: ${material.fingerprint}\nDataset: ${currentMaterial.label}\nDataset scope: ${currentMaterial.notice}\nDisplayed record snapshot:\n${JSON.stringify(row, null, 2)}`
    if (id === 126 && material.checks) snapshot = `\n\nNews quality checks: ${JSON.stringify(material.checks)}${snapshot}`
    if (id === 128 && material.editorialChecks) snapshot = `\n\nOriginals editorial checks: ${JSON.stringify(material.editorialChecks)}${snapshot}`
    if (snapshot.length > 40000) throw new Error("Record too large for a review comment")
  }
  const current = await getTaskReview(id)
  const latest = current.history.at(-1)?.id || 0
  if (`${current.issue.updated_at}:${latest}` !== version || current.issue.state !== "open") throw new Error("Review changed; reload before saving")
  const { data, error } = await (await createClient()).auth.getUser()
  if (error || !data.user) throw new Error("Sign in required")
  const saved = await github(`/issues/${id}/comments`, JSON.stringify({ body: `${MARKER}\n\nDecision: ${decision}\nReviewer (verified Dadspace user): ${data.user.id}\nReviewed issue version: ${version}\n\nScope / reason / follow-up:\n${notes.trim()}\n\nEvidence / sample IDs:\n${evidence.trim() || "Not supplied"}${snapshot}\n\nRecorded through /ops/reviews/${id}. This records a human decision only; outstanding acceptance, data application and release gates remain open.` })) as Comment
  return saved.id
}

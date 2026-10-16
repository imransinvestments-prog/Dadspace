import { createHash } from "node:crypto"
import sample from "@/artefacts/data/news-quality-sample-2026-10-15.json"

export const NEWS_SAMPLE = sample
import { NEWS_EXTRA_KEYS, UNKNOWN_NEWS_CHECKS, validNewsChecks, type NewsChecks } from "./news-checks"
export { UNKNOWN_NEWS_CHECKS, validNewsChecks, type NewsChecks } from "./news-checks"
const hash = (row: unknown) => createHash("sha256").update(JSON.stringify(row)).digest("hex")
type ReviewComment = { id: number; body: string; user: { login: string } }
export function newsProgress(comments: ReviewComment[]) {
  const latest = new Map<string, { decision: string; checks: NewsChecks; commentId: number }>()
  const supplements = new Map<string, { commentId: number; checks: Partial<NewsChecks> }>()
  for (const comment of [...comments].sort((a, b) => a.id - b.id)) {
    if (comment.user.login.toLowerCase() === "imransinvestments-prog" && comment.body.startsWith("Dadspace news supplemental review v1\n")) {
      try {
        const payload=JSON.parse(comment.body.match(/^News supplemental checks: (\{[^\n]+\})$/m)?.[1] || "null")
        if (payload?.sampleId === sample.id && Array.isArray(payload.records) && payload.records.length <= 50) for(const record of payload.records) {
          const row=sample.rows.find(row=>row.id===record.id)
          if (!row || hash(row)!==record.fingerprint || !record.checks || !NEWS_EXTRA_KEYS.every(key=>["yes","no","unknown"].includes(record.checks[key]))) continue
          supplements.set(row.id,{commentId:comment.id,checks:Object.fromEntries(NEWS_EXTRA_KEYS.map(key=>[key,record.checks[key]]))})
        }
      } catch { /* Malformed or unrelated confirmations never count. */ }
      continue
    }
    // Only the repository owner's audit comments with an exact frozen/legacy
    // snapshot count. Arbitrary public comments and task-wide approvals do not.
    if (comment.user.login.toLowerCase() !== "imransinvestments-prog" || !comment.body.startsWith("Dadspace owner review v1\n")) continue
    const id = comment.body.match(/^Reviewed record: (\d+)$/m)?.[1]
    const fingerprint = comment.body.match(/^Snapshot SHA-256: ([a-f0-9]{64})$/m)?.[1]
    const decision = comment.body.match(/^Decision: (.+)$/m)?.[1]
    if (!id || !fingerprint || !decision || !["Approved for stated scope", "Changes requested", "Blocked — more evidence needed"].includes(decision)) continue
    const row = sample.rows.find(row => row.id === id)
    if (!row) continue
    const legacy = sample.legacy_rows.find(row => row.id === id)
    if (hash(row) !== fingerprint && (!legacy || hash(legacy) !== fingerprint)) continue
    let checks: NewsChecks = { ...UNKNOWN_NEWS_CHECKS }
    try {
      const parsed = JSON.parse(comment.body.match(/^News quality checks: (\{[^\n]+\})$/m)?.[1] || "null")
      if (validNewsChecks(parsed) && hash(row) === fingerprint) checks = { ...UNKNOWN_NEWS_CHECKS, ...parsed }
    } catch { /* Older notes remain decisions, never invented rubric scores. */ }
    latest.set(id, { decision, checks, commentId: comment.id })
  }
  for(const [id, supplement] of supplements) {
    const review=latest.get(id)
    if(review && supplement.commentId > review.commentId) review.checks={...review.checks,...supplement.checks}
  }
  const reviews = Object.fromEntries(latest)
  const values = [...latest.values()]
  const yes = (key: keyof NewsChecks) => values.filter(row => row.checks[key] === "yes").length
  const checked = (key: keyof NewsChecks) => values.filter(row => row.checks[key] !== "unknown").length
  return { reviews, reviewed: latest.size, remaining: sample.rows.length - latest.size,
    relevantAndAttributed: values.filter(row => row.checks.relevance === "yes" && row.checks.attribution === "yes").length,
    relevanceChecked: checked("relevance"), attributionChecked: checked("attribution"),
    linksWorking: yes("destination"), linksChecked: checked("destination"),
    geographyCorrect: yes("geography"), geographyChecked: checked("geography"),
    summariesAccepted: yes("summary"), datesAccepted: yes("date"), sensitiveLabelsAccepted: yes("sensitiveLabel"), homepagePicksAccepted: yes("homepagePick") }
}
export function newsGeography(fields: Record<string, unknown>) {
  const scope = typeof fields.geo_scope === "string" ? fields.geo_scope : "unknown"
  const area = [fields.region, fields.geo_region, fields.admin_area, fields.locality].filter(value => typeof value === "string" && value).join(" · ")
  return { scope, area: area || "Area not recorded", guidance: scope === "local" ? "Judge usefulness for families in this locality; it does not need to be relevant nationwide." : scope === "regional" ? "Judge usefulness for families in the named region." : scope === "nationwide" ? "Stored as nationwide. Check whether the story is actually national in scope." : "Geographic scope is missing. Check the publisher's article; do not assume nationwide relevance.", limitation: "Stored targeting metadata is shown here. This does not prove which readers actually saw the story; verify the public location filters separately." }
}

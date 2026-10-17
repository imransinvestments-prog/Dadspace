import "server-only"
import { createHash } from "node:crypto"
import { DEAL_CHECK_LABELS, validDealChecks, type DealChecks } from "./deal-check-labels"
import pack from "@/artefacts/data/sprint5-review-pack.json"
export function dealProgress(comments: { id: number; body: string; user: { login: string } }[]) {
  const reviews: Record<string, { checks: DealChecks; commentId: number }> = {}
  for (const comment of [...comments].sort((a,b)=>a.id-b.id)) {
    if (comment.user.login.toLowerCase() !== "imransinvestments-prog" || !comment.body.startsWith("Dadspace owner review v1\n")) continue
    const id=comment.body.match(/^Reviewed record: (\d+)$/m)?.[1]
    const fingerprint=comment.body.match(/^Snapshot SHA-256: ([a-f0-9]{64})$/m)?.[1]
    const row=pack.deals.rows.find(row=>row.id===id)
    if(!id || !row || createHash("sha256").update(JSON.stringify(row)).digest("hex")!==fingerprint) continue
    // A later decision with no detailed checks supersedes old detail scores.
    delete reviews[id]
    try {
      const checks=JSON.parse(comment.body.match(/^Deal quality checks: (\{[^\n]+\})$/m)?.[1]||"null")
      if(validDealChecks(checks)) reviews[id]={checks,commentId:comment.id}
    } catch { /* Unknown is never a pass. */ }
  }
  const values=Object.values(reviews)
  const passed=(value: {checks:DealChecks})=>Object.keys(DEAL_CHECK_LABELS).every(key=>value.checks[key as keyof DealChecks]==="yes")
  const topIds=new Set(pack.deals.rows.slice(0,20).map(row=>row.id))
  return { reviews, denominator:pack.deals.rows.length, checked:values.length, allChecksPassed:values.filter(passed).length,
    topDenominator:topIds.size, topPassed:Object.entries(reviews).filter(([id,value])=>topIds.has(id)&&passed(value)).length,
    knownFailures:values.filter(value=>Object.values(value.checks).includes("no")).length }
}

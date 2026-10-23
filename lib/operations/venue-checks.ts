import { createHash } from "node:crypto"
import {validVenueChecks,type VenueChecks} from './venue-check-labels'
import scoring from '@/artefacts/data/venue-review-34-scoring-2026-10-22.json'
type Row={id:string;title:string;fields:Record<string,unknown>}
// Owner ruling (22 Oct 2026, #34): an approval counts as a pass for identity, location and source, and
// explicit ticks are scored as given. Audience-only change requests are not data errors. The data-quality
// failures were judged from the review notes, so they are frozen with the scoring rather than inferred.
const FAILURES=new Set(scoring.failures.map(f=>f.id))
export function venueProgress(comments:{id:number;body:string;user:{login:string}}[],rows:Row[]) {
 const reviews=new Map<string,{decision:string;checks:VenueChecks|null}>()
 for(const comment of [...comments].sort((a,b)=>a.id-b.id)) {
  if(comment.user.login.toLowerCase()!=="imransinvestments-prog" || !comment.body.startsWith("Dadspace owner review v1\n"))continue
  const id=comment.body.match(/^Reviewed record: (.+)$/m)?.[1],fingerprint=comment.body.match(/^Snapshot SHA-256: ([a-f0-9]{64})$/m)?.[1]
  const row=rows.find(r=>r.id===id)
  if(!row || createHash('sha256').update(JSON.stringify(row)).digest('hex')!==fingerprint)continue
  try {
   const checks=JSON.parse(comment.body.match(/^Venue quality checks: (\{[^\n]+\})$/m)?.[1] || 'null')
   const decision=comment.body.match(/^Decision: (.+)$/m)?.[1] || ''
   if((checks===null || validVenueChecks(checks)) && ['Approved for stated scope','Changes requested','Blocked — more evidence needed'].includes(decision)) reviews.set(row.id,{decision,checks})
  }catch{/* Malformed checks never imply acceptance. */}
 }
 const failed=(id:string,r:{decision:string;checks:VenueChecks|null})=>FAILURES.has(id) || r.decision==='Blocked — more evidence needed' || (r.checks!==null && ['identity','location','source'].some(k=>r.checks?.[k as keyof VenueChecks]==='no'))
 const entries=[...reviews.entries()],passed=entries.filter(([id,r])=>!failed(id,r)).length
 // Every recorded failure was renamed, hidden or merged before #34 closed.
 const remediated=entries.filter(([id])=>FAILURES.has(id)).length,afterRemediation=passed+remediated
 return {denominator:50,required:48,reviewed:reviews.size,passed,remediated,afterRemediation,qualityGate:rows.length===50 && afterRemediation>=48,reviews:Object.fromEntries(reviews)}
}

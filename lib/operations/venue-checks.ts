import { createHash } from "node:crypto"
import {validVenueChecks,type VenueChecks} from './venue-check-labels'
type Row={id:string;title:string;fields:Record<string,unknown>}
export function venueProgress(comments:{id:number;body:string;user:{login:string}}[],rows:Row[]) {
 const reviews=new Map<string,{decision:string;checks:VenueChecks}>()
 for(const comment of [...comments].sort((a,b)=>a.id-b.id)) {
  if(comment.user.login.toLowerCase()!=="imransinvestments-prog" || !comment.body.startsWith("Dadspace owner review v1\n"))continue
  const id=comment.body.match(/^Reviewed record: (.+)$/m)?.[1],fingerprint=comment.body.match(/^Snapshot SHA-256: ([a-f0-9]{64})$/m)?.[1]
  const row=rows.find(r=>r.id===id)
  if(!row || createHash('sha256').update(JSON.stringify(row)).digest('hex')!==fingerprint)continue
  try {
   const checks=JSON.parse(comment.body.match(/^Venue quality checks: (\{[^\n]+\})$/m)?.[1] || 'null')
   const decision=comment.body.match(/^Decision: (.+)$/m)?.[1] || ''
   if(validVenueChecks(checks) && ['Approved for stated scope','Changes requested','Blocked — more evidence needed'].includes(decision)) reviews.set(row.id,{decision,checks})
  }catch{/* Missing or malformed checks never imply acceptance. */}
 }
 const passed=[...reviews.values()].filter(r=>r.decision==='Approved for stated scope' && r.checks.identity==='yes' && r.checks.location==='yes' && r.checks.source==='yes').length
 return {denominator:50,required:48,reviewed:reviews.size,passed,qualityGate:rows.length===50 && passed>=48,reviews:Object.fromEntries(reviews)}
}

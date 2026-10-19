// Explicitly accepted area/category cohorts only. Browse supply is independent of SEO approval.
export type PublicationApproval = {
 area: string; category: string; approvedBy: string; approvedAt: string;
 // Every currently listed venue must still match its approved public facts.
 venues: { id: string; fingerprint: string }[];
}
export const DISCOVERY_APPROVALS: PublicationApproval[] = []

export function discoveryPublicationReady(area: string, category: string, rows: {id: string; fingerprint: string}[], total: number, failed: boolean, approvals = DISCOVERY_APPROVALS) {
 if (failed || !Number.isSafeInteger(total) || total < 3 || rows.length !== total || new Set(rows.map(r=>r.id)).size !== total) return false
 const approval=approvals.find(a=>a.area===area && a.category===category)
 if (!approval || !approval.approvedBy.trim() || !Number.isFinite(Date.parse(approval.approvedAt)) || approval.venues.length!==total || new Set(approval.venues.map(r=>r.id)).size!==total) return false
 const expected=new Map(approval.venues.map(r=>[r.id,r.fingerprint]))
 return rows.every(r=>!!r.fingerprint && expected.get(r.id)===r.fingerprint)
}

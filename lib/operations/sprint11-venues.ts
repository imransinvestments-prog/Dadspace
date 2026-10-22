import pack from '@/artefacts/data/sprint5-review-pack.json'
import current from '@/artefacts/data/sprint11-venues-snapshot.json'
import labels from '@/artefacts/data/sprint11-venue-labels.json'
// Keep every original identity and original evidence. Current projection is an additional dated snapshot.
export const SPRINT11_VENUE_ROWS=pack.venues.rows.map(row=>({
 ...row,fields:{...row.fields,current_snapshot:current.rows.find(v=>v.id===row.id) || null,
 current_label:labels.find(v=>v.id===row.id)?.venue_label || null,
 current_captured_at:current.captured_at,
 scoring:"Identity, location and usable primary evidence must all pass for 48/50. Access, facts and image rights remain explicit. This snapshot is not live verification."}
}))

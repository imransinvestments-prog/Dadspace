import pack from '@/artefacts/data/sprint5-review-pack.json'
import current from '@/artefacts/data/sprint11-venues-snapshot.json'
import labels from '@/artefacts/data/sprint11-venue-labels.json'
import sample from '@/artefacts/data/venue-review-sample-2026-10-22.json'
// Keep every original identity and original evidence. Current projection is an additional dated snapshot.
export const SPRINT11_VENUE_ROWS=pack.venues.rows.map(row=>({
 ...row,fields:{...row.fields,current_snapshot:current.rows.find(v=>v.id===row.id) || null,
 current_label:labels.find(v=>v.id===row.id)?.venue_label || null,
 current_captured_at:current.captured_at,
 scoring:"Identity, location and usable primary evidence must all pass for 48/50. Access, facts and image rights remain explicit. This snapshot is not live verification."}
}))
// #34 as scored (closed 22 Oct 2026): the 25 originals reviewed from the 17 Oct sample, unchanged so their
// saved fingerprints still match, then the 25-venue replacement drawn on 22 Oct.
export const REVIEW34_ROWS=[...SPRINT11_VENUE_ROWS.filter(row=>sample.retained_original_ids.includes(row.id)),...sample.rows]

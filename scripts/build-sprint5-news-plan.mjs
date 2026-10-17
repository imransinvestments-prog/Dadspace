// Generate a review-only plan. Does not connect to a database or apply changes.
import fs from 'node:fs'
import { createHash } from 'node:crypto'
const evidence = JSON.parse(fs.readFileSync('artefacts/data/sprint5-news-evidence.json', 'utf8'))
const hash = value => createHash('sha256').update(JSON.stringify(value)).digest('hex')
const current = [...evidence.rows, ...evidence.additional_negative_geography.rows]
const national = new Set([306,321,362,378,453,474,486,630,653,808,877])
const local = {
  430: { region:'england',admin_area:'hampshire',locality:null },
  909: { region:'wales',admin_area:null,locality:'monmouthshire' },
  328: { region:'england',admin_area:null,locality:'west_northamptonshire' },
  739: { region:'england',admin_area:'cheshire',locality:null },
  596: { region:'england',admin_area:null,locality:'sunderland' },
  708: { region:'england',admin_area:null,locality:'redditch' },
  342: { region:'england',admin_area:null,locality:'cambridge' },
}
const rows = current.map(before => {
  const id = before.id
  const comment = evidence.owner_decisions.filter(c => c.body.includes(`Reviewed record: ${id}\n`)).at(-1)
  const notes = comment?.body.match(/Scope \/ reason \/ follow-up:\n([\s\S]*?)\n\nEvidence \/ sample IDs:/)?.[1] ?? 'Not supplied'
  let after = null, reason = ''
  if (national.has(id)) { after = {...before,geo_scope:'nationwide',geo_region:null,admin_area:null,locality:null}; reason='Follow the owner nationwide-scope instruction; preserve the recorded nation. Nationwide within England/Wales is not automatically UK-wide.' }
  if (local[id]) { after={...before,geo_scope:'local',geo_region:null,...local[id]}; reason='Map the owner place instruction into the existing nation/county/district contract; do not put a town in region.' }
  if(id===909) reason='Already Monmouthshire in current row. Recommend retaining the county-wide target rather than narrowing to Monmouth town; needs confirmation.'
  if(id===739) { after=null; reason='Cheshire is not one current council district. Confirm county-wide intent and supported geography token before proposing an executable change.' }
  if(id===736) reason='Owner asks Glasgow; stored title/summary say Port Glasgow. Hold until source evidence resolves intended location; do not silently substitute Glasgow City.'
  if(id===855) reason='Owner asks Colchester; destination URL names Maldon. Hold until source evidence confirms locality and whether the general support story stays national.'
  const fields={owner_request:notes,reason,before,proposed:after,source_url:before.url,owner_decision_url:comment?.html_url??null,changed:after!==null&&hash(after)!==hash(before),status:after===null?'Hold — location evidence/owner decision required':'Proposed only — not applied',before_sha256:hash(before)}
  return {id:String(id),title:before.title,fields}
})
const plan={captured_at:evidence.captured_at,scope:'18 requested changes plus two negative geography labels; original 50-row News reviews remain immutable.',rows}
fs.writeFileSync('artefacts/data/sprint5-news-corrections.json',JSON.stringify(plan,null,2)+'\n')
console.log(JSON.stringify({rows:rows.length,proposed:rows.filter(r=>r.fields.changed).length,holds:rows.filter(r=>r.fields.proposed===null).map(r=>r.id),unchanged:rows.filter(r=>r.fields.proposed!==null&&!r.fields.changed).map(r=>r.id)}))

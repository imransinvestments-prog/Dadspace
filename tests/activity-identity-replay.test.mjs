import { test } from 'node:test'
import assert from 'node:assert/strict'
import { replayIdentity } from '../scripts/replay-activity-identity.mjs'

test('source-backed real SQL replay verifies stable imports and reproduces bounded identity gaps',async()=>{
  const result = await replayIdentity()
  const cases = Object.fromEntries(result.cases.map(row=>[row.case,row]))
  assert.equal(cases.repeat_import.rows,1)
  assert.equal(cases.repeat_import.same_id,true)
  assert.equal(cases.repeat_import.same_identity,true)
  assert.equal(cases.repeat_import.same_content,true)
  assert.equal(cases.changed_schedule.same_id,true)
  assert.equal(cases.changed_schedule.same_identity,true)
  assert.equal(cases.changed_schedule.content_changed,true)
  assert.equal(cases.distinct_named_programmes_same_venue.rows,2)
  assert.equal(cases.moved_programme.rows,2)
  // Reproductions retained until an explicitly reviewed repair changes policy.
  assert.equal(cases.renamed_programme_same_url.rows,2)
  assert.equal(cases.distinct_same_title_same_venue_sessions.rows,1)
})

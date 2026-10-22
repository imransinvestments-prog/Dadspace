import { test } from 'node:test'
import assert from 'node:assert/strict'
import { rehearseProviderIdentity } from '../scripts/rehearse-provider-identity.mjs'

test('review-gated provider identity preserves collector compatibility and refuses stale inverses',async()=>{
  const report=await rehearseProviderIdentity()
  assert.equal(report.cases.length,15)
  for(const result of report.cases) assert.equal(result.pass,true,result.case)
  assert.equal(report.production_writes,0)
})

const assert = require('node:assert/strict')
const { test } = require('node:test')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, deps = {}, extra = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, require: name => deps[name] ?? require(name), process: { env: {} }, AbortSignal, ...extra })
  return module.exports
}
const tasks = load('lib/operations/review-tasks.ts')
const access = load('lib/operations/access.ts')
const uid = '12345678-1234-1234-1234-123456789abc'
function harness({ allowed = 'allowed', reviewer = true, changed = false, token = 'test-only', materialChanged = false } = {}) {
  const calls = []
  const api = load('lib/operations/task-review.ts', {
    'server-only': {}, './session': { operationsAccess: async () => allowed }, './access': access,
    './review-tasks': tasks, '@/lib/supabase/server': { createClient: async () => ({ auth: { getUser: async () => ({ data: { user: { id: uid } } }) } }) },
    './review-material': { getReviewMaterial: async () => ({ available: true, label: 'Live news', notice: 'Not a frozen sample', rows: [{ id: 'record-1', title: 'Article', fields: { summary: 'Actual evidence' } }] }), materialFingerprint: () => materialChanged ? 'changed' : 'snapshot-hash' },
  }, { process: { env: { DADSPACE_REVIEWER_USER_IDS: reviewer ? uid : '', DADSPACE_REVIEW_GITHUB_TOKEN: token } },
    fetch: async (url, options) => { calls.push({ url, options }); return { ok: true, json: async () => options.method === 'POST' ? { id: 99 } : url.includes('/comments?') ? [] : { state: 'open', updated_at: changed ? 'new' : 'old' } } },
  })
  return { api, calls }
}
test('read access is checked before fetching GitHub evidence', async () => {
  const { api, calls } = harness({ allowed: 'denied' })
  await assert.rejects(api.getTaskReview(123)); assert.equal(calls.length, 0)
})
test('operators do not inherit reviewer writes', async () => {
  const { api, calls } = harness({ reviewer: false })
  await assert.rejects(api.recordTaskReview(123, tasks.REVIEW_DECISIONS[0], 'scope', 'sample', 'old:0'))
  assert.equal(calls.length, 0)
})
test('invalid task, decision and oversized input cannot write', async () => {
  const { api, calls } = harness()
  for (const args of [[999, tasks.REVIEW_DECISIONS[0], 'scope'], [123, 'close issue', 'scope'], [123, tasks.REVIEW_DECISIONS[0], 'x'.repeat(6001)]]) await assert.rejects(api.recordTaskReview(...args, '', 'old:0'))
  assert.equal(calls.length, 0)
})
test('stale issue evidence prevents posting a decision', async () => {
  const { api, calls } = harness({ changed: true })
  await assert.rejects(api.recordTaskReview(123, tasks.REVIEW_DECISIONS[0], 'scope', 'sample', 'old:0'))
  assert.equal(calls.some(c => c.options.method === 'POST'), false)
})
test('review records actor scope and evidence without closing or changing issue criteria', async () => {
  const { api, calls } = harness()
  assert.equal(await api.recordTaskReview(123, tasks.REVIEW_DECISIONS[1], 'Correct the sample', 'IDs 1–50', 'old:0'), 99)
  const writes = calls.filter(c => c.options.method === 'POST')
  assert.equal(writes.length, 1); assert.ok(writes[0].url.endsWith('/issues/123/comments'))
  const body = JSON.parse(writes[0].options.body).body
  assert.ok(body.includes(uid)); assert.ok(body.includes('Correct the sample')); assert.ok(body.includes('IDs 1–50')); assert.ok(body.includes('release gates remain open'))
})
test('readiness reports missing token and reviewer setup separately', async () => {
  const { api } = harness({ reviewer: false, token: '' })
  const result = await api.reviewReadiness()
  assert.equal(result.canSave, false)
  assert.ok(result.reasons.some(reason => reason.includes('DADSPACE_REVIEW_GITHUB_TOKEN')))
  assert.ok(result.reasons.some(reason => reason.includes('DADSPACE_REVIEWER_EMAILS')))
})
test('changed record snapshot prevents a review even when issue version matches', async () => {
  const { api, calls } = harness({ materialChanged: true })
  await assert.rejects(api.recordTaskReview(126, tasks.REVIEW_DECISIONS[0], 'Record scope', '', 'old:0', { rowId: 'record-1', page: 1, fingerprint: 'snapshot-hash' }))
  assert.equal(calls.some(c => c.options.method === 'POST'), false)
})
test('record decision includes the server-verified snapshot and dataset scope', async () => {
  const { api, calls } = harness()
  await api.recordTaskReview(126, tasks.REVIEW_DECISIONS[1], 'Correct attribution', '', 'old:0', { rowId: 'record-1', page: 1, fingerprint: 'snapshot-hash' })
  const body = JSON.parse(calls.find(c => c.options.method === 'POST').options.body).body
  assert.ok(body.includes('Actual evidence')); assert.ok(body.includes('snapshot-hash')); assert.ok(body.includes('Not a frozen sample'))
})
test('approval succeeds without additional evidence and records it as not supplied', async () => {
  const { api, calls } = harness()
  assert.equal(await api.recordTaskReview(126, tasks.REVIEW_DECISIONS[0], 'Relevant article', '', 'old:0', { rowId: 'record-1', page: 1, fingerprint: 'snapshot-hash' }), 99)
  const body = JSON.parse(calls.find(c => c.options.method === 'POST').options.body).body
  assert.ok(body.includes('Evidence / sample IDs:\nNot supplied'))
})

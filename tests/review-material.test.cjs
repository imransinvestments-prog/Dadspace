const assert = require('node:assert/strict')
const { test } = require('node:test')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const ts = require('typescript')
function harness({ access = 'allowed', configured = true, failed = false, data = [], count = data.length } = {}) {
  const calls = []
  const query = new Proxy({}, { get: (_, key) => key === 'then' ? resolve => resolve({ data, count, error: failed ? {} : null }) : (...args) => { calls.push([key, ...args]); return query } })
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync('lib/operations/review-material.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, process: { env: configured ? { DADSPACE_SUPABASE_SERVICE_ROLE_KEY: 'test-only' } : {} }, AbortSignal,
    require: name => {
      if (name === 'server-only') return {}
      if (name === './session') return { operationsAccess: async () => access }
      if (name === '@/lib/supabase') return { getSupabase: () => ({ from: table => { calls.push(['from', table]); return query } }) }
      if (name === '@/lib/deals') return { getDeals: async () => ({ loadFailed: false, items: [] }) }
      if (name === './review-tasks') return { reviewTask: id => [34,123,126,128,130,135,136,145,149].includes(id) }
      if (name === './processes') return { OPERATIONS_PROCESSES: Array.from({ length: 11 }, (_, i) => ({ name: `Process ${i + 1}`, owner: 'Owner' })) }
      if (name.startsWith('@/artefacts/')) return JSON.parse(fs.readFileSync(path.join(process.cwd(), name.slice(2)), 'utf8'))
      return require(name)
    } })
  return { api: module.exports, calls }
}
test('unauthorized readers cannot query review records', async () => {
  const { api, calls } = harness({ access: 'denied' })
  await assert.rejects(api.getReviewMaterial(126)); assert.equal(calls.length, 0)
})
test('missing service credential and query failures are unavailable rather than empty', async () => {
  assert.equal((await harness({ configured: false }).api.getReviewMaterial(126)).available, false)
  assert.equal((await harness({ failed: true }).api.getReviewMaterial(126)).available, false)
})
test('news records retain actual content and deterministic bounded pagination', async () => {
  const { api, calls } = harness({ data: [{ id: 42, title: 'Article', summary: 'Full review text' }], count: 11 })
  const result = await api.getReviewMaterial(126, 2)
  assert.equal(result.available, true); assert.equal(result.rows[0].fields.summary, 'Full review text')
  assert.ok(calls.some(call => call[0] === 'range' && call[1] === 10 && call[2] === 19))
  assert.equal(result.total, 11); assert.ok(result.notice.includes('not a frozen'))
})
test('partial pages cannot silently drop records', async () => {
  const { api } = harness({ data: [{ id: 42, title: 'Article' }], count: 15 })
  assert.equal((await api.getReviewMaterial(126, 1)).available, false)
})
test('operations inventory is reviewable per process and page two retains eleventh process', async () => {
  const { api } = harness()
  const result = await api.getReviewMaterial(149, 2)
  assert.equal(result.total, 11); assert.equal(result.rows.length, 1); assert.equal(result.rows[0].title, 'Process 11')
})
test('saved source proposals and provider source text are actual dated evidence', async () => {
  const { api } = harness()
  const historical = await api.getReviewMaterial(135)
  assert.ok(historical.rows[0].fields.recommendation); assert.ok(historical.notice.includes('not current'))
  const provider = await api.getReviewMaterial(145)
  assert.equal(provider.total, 4); assert.ok(provider.rows[0].fields.source_text.includes('Unity FC'))
})

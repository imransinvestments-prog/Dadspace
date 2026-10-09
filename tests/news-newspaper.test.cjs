const assert = require('node:assert/strict')
const { test } = require('node:test')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, dependencies = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, process, Intl, Date, require: name => name === 'next/cache' ? { unstable_cache: fn => fn } : dependencies[name] ?? require(name) })
  return module.exports
}
const { newsMonth } = load('lib/news-month.ts')
test('London month boundaries include BST and December rollover', () => {
  assert.equal(newsMonth(new Date('2026-03-31T23:30:00Z')).start, '2026-03-31T23:00:00.000Z')
  assert.equal(newsMonth(new Date('2026-03-31T23:30:00Z')).end, '2026-04-30T23:00:00.000Z')
  assert.equal(newsMonth(new Date('2026-10-09T12:00:00Z')).end, '2026-11-01T00:00:00.000Z')
  assert.equal(newsMonth(new Date('2026-12-20T12:00:00Z')).end, '2027-01-01T00:00:00.000Z')
})
test('monthly counts are exact, primary, relevant, ingestion-based and not truncated', async () => {
  process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY = 'test-server-key'
  const calls = []
  const db = { from(table) {
    assert.equal(table, 'news_items')
    const query = {}
    for (const method of ['select', 'eq', 'gte', 'lt', 'or']) query[method] = (...args) => { calls.push([method, ...args]); return query }
    query.then = resolve => resolve({ count: 2501, error: null })
    return query
  } }
  const { getMonthlyNews } = load('lib/news-monthly.ts', { 'server-only': {}, './supabase': { getSupabase: () => db }, './news-month': { newsMonth: () => ({start:'start',end:'end',label:'October 2026'}) }, './news': { CATEGORIES: [{value:'all'}, {value:'safety'}] } })
  assert.equal((await getMonthlyNews()).counts.safety, 2501)
  assert.equal(calls.find(c => c[0] === 'select')[2].head, true)
  assert.equal(calls.find(c => c[0] === 'select')[2].count, 'exact')
  assert.ok(calls.some(c => c.join('|') === 'gte|created_at|start'))
  assert.ok(calls.some(c => c.join('|') === 'lt|created_at|end'))
  assert.ok(calls.some(c => c.join('|') === 'gte|relevance|3'))
  assert.ok(calls.some(c => c.join('|') === 'or|is_primary.eq.true,is_primary.is.null'))
  delete process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY
  assert.equal((await getMonthlyNews()).counts, null)
})
test('query failure is unavailable and a genuine empty month is zero', async () => {
  process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY = 'test-server-key'
  let result = { count: 0, error: null }
  const q = { select:()=>q, eq:()=>q, gte:()=>q, lt:()=>q, or:()=>q, then:resolve=>resolve(result) }
  const { getMonthlyNews } = load('lib/news-monthly.ts', { 'server-only': {}, './supabase': { getSupabase: () => ({from:()=>q}) }, './news-month': { newsMonth }, './news': { CATEGORIES: [{value:'safety'}] } })
  assert.equal((await getMonthlyNews()).counts.safety, 0)
  result = { count: null, error: { message: 'offline' } }
  assert.equal((await getMonthlyNews()).counts, null)
  delete process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY
})

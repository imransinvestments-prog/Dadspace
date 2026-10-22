const assert = require('node:assert/strict')
const { test } = require('node:test')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, dependencies = {}, env = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, process: { env }, Date, Number, Promise, AbortSignal, URL,
    require: name => dependencies[name] ?? require(name) })
  return module.exports
}
const shared = load('lib/operations/evidence-shared.ts')
test('source checks, failures, zero yield and unknown yield remain independent', () => {
  const source = { active: true, checked: '2026-10-14T07:00:00Z', failures: 0, failed: false, yield: 0, yieldLabel: 'reported listings' }
  const now = new Date('2026-10-14T12:00:00Z')
  let result = shared.sourceSignals(source, now)
  assert.equal(result.collection, 'No failure recorded')
  assert.equal(result.yield, 'Zero observed yield')
  assert.equal(result.attention, true)
  result = shared.sourceSignals({ ...source, failed: true, yield: 4 }, now)
  assert.equal(result.collection, 'Failure recorded')
  assert.equal(result.freshness, 'Checked within 36h')
  assert.equal(result.yield, '4 reported listings')
  assert.equal(shared.sourceSignals({ ...source, checked: null, yield: null }, now).yield, 'Unknown')
  assert.equal(shared.sourceSignals({ ...source, checked: '2026-10-12T07:00:00Z' }, now).freshness, 'Check overdue')
  assert.equal(shared.sourceSignals({ ...source, active: false }, now).collection, 'Inactive')
})
test('queue inputs are bounded and links cannot execute scripts or expose signed query credentials', () => {
  for (const page of ['0', '-1', '1e6', '10000', ['2'], "1;drop table venues"]) assert.equal(shared.reviewQuery('venues', page).page, 1)
  assert.equal(shared.reviewQuery('activities', '2').page, 2)
  assert.equal(shared.reviewQuery(['events'], '1').kind, 'venues')
  for (const link of ['javascript:alert(1)', 'data:text/html,test', 'https://user:pass@example.com/', '/relative']) assert.equal(shared.evidenceUrl(link), null)
  assert.equal(shared.evidenceUrl('https://example.com/detail?token=secret#track'), 'https://example.com/detail')
  assert.equal(shared.evidenceUrl('https://example.com/event?id=320734&token=secret'), 'https://example.com/event?id=320734')
  assert.equal(shared.evidenceUrl('https://www.matalan.co.uk/p/uniform/14894526/?variation=14894527&token=secret'), 'https://www.matalan.co.uk/p/uniform/14894526/?variation=14894527')
  assert.equal(shared.evidenceUrl('https://example.com/detail?variation=secret'), 'https://example.com/detail')
  assert.equal(shared.evidenceUrl('https://www.matalan.co.uk/p/uniform/14894526/?variation=secret'), 'https://www.matalan.co.uk/p/uniform/14894526/')
})
function database(access, responseFor, configured = true) {
  const queries = []
  let clients = 0
  const db = { from: table => {
    const record = { table, filters: [], orders: [] }; queries.push(record)
    const builder = {
      select: (fields, options) => { record.fields = fields; record.options = options; return builder },
      eq: (field, value) => { record.filters.push(['eq', field, value]); return builder },
      is: (field, value) => { record.filters.push(['is', field, value]); return builder },
      or: filter => { record.filters.push(['or', filter]); return builder },
      order: field => { record.orders.push(field); return builder },
      range: (first, last) => { record.range = [first, last]; return builder },
      abortSignal: () => builder,
      then: (resolve, reject) => Promise.resolve().then(() => responseFor(record)).then(resolve, reject),
    }; return builder
  } }
  const module = load('lib/operations/database.ts', { 'server-only': {}, './session': { operationsAccess: async () => access },
    './evidence-shared': shared, '@/lib/supabase': { getSupabase: () => { clients++; return db } } }, configured ? { DADSPACE_SUPABASE_SERVICE_ROLE_KEY: 'server-test-only' } : {})
  return { module, queries, clients: () => clients }
}
test('every private entry point gates reads and missing service configuration is unavailable, never empty', async () => {
  for (const access of ['denied', 'sign-in', 'unavailable']) {
    const test = database(access, () => { throw new Error('must not read') })
    assert.equal((await test.module.getDatabaseEvidence()).access, access)
    assert.equal((await test.module.getReviewQueue()).access, access)
    assert.equal(test.clients(), 0)
    assert.equal(test.queries.length, 0)
  }
  const test = database('allowed', () => { throw new Error('must not read') }, false)
  assert.equal((await test.module.getDatabaseEvidence()).available, false)
  assert.equal((await test.module.getReviewQueue()).result.available, false)
  assert.equal(test.clients(), 0)
})
test('partial database failure retains other metrics and incomplete source rows are never reported as complete', async () => {
  const test = database('allowed', record => {
    if (record.table === 'sources') return { data: [], count: 501, error: null }
    if (record.table === 'current_activities') throw new Error('timeout with private details')
    if (record.table === 'deal_sources') return { data: [{ id: 37, name: 'Merchant', active: true, last_status: 'http_500', consecutive_failures: 1, last_counts: { verified: 0, rejected: { secret: 2 } } }], count: 1, error: null }
    if (record.table === 'news_sources') return { data: [], count: 0, error: null }
    return { data: null, count: 0, error: null }
  })
  const result = await test.module.getDatabaseEvidence()
  assert.equal(result.discovery.available, false)
  assert.equal(result.activities.available, false)
  assert.equal(result.venues.value, 0)
  assert.equal(result.deals.value[0].failed, true)
  assert.equal(JSON.stringify(result).includes('secret'), false)
  assert.equal(JSON.stringify(result).includes('private details'), false)
  assert.equal(test.queries.every(q => !q.fields.includes('*')), true)
  assert.equal(test.queries.find(q => q.table === 'sources').range[1], 499)
})
test('unnamed hidden venues remain reviewable without invalidating the queue', async () => {
  const fixture = database('allowed', () => ({ data: [{ id: 'unnamed', venue_name: null }, { id: 'named', venue_name: 'Library' }], count: 2, error: null }))
  const result = (await fixture.module.getReviewQueue('venues')).result
  assert.equal(result.available, true)
  assert.equal(result.value.total, 2)
  assert.equal(result.value.rows[0].title, 'Unnamed venue — identity evidence missing')
  assert.equal(result.value.rows[1].title, 'Library')
  // Arcades decided by evidence never queue; arcades hidden by the 22 Oct rule wait for the owner;
  // prison libraries hidden as not open to the public are decided and never queue.
  const filters = fixture.queries.find(q => q.table === 'venues').filters.filter(f => f[0] === 'or').map(f => f[1])
  assert.deepEqual(filters, ['category.neq."Amusement arcade",adult_only.is.null',
    'review_reason.is.null,review_reason.not.ilike."*2026-10-22 owner rule: amusement arcades*"',
    'review_reason.is.null,review_reason.not.ilike."*Owner decision 2026-10-22: not open to the public*"'])
  const labelled = database('allowed', () => ({ data: [{ id: 'p', venue_name: null, venue_label: 'Church Lane Playground' }], count: 1, error: null }))
  assert.equal((await labelled.module.getReviewQueue('venues')).result.value.rows[0].title, 'Church Lane Playground (derived label; no source name)')
  const invalid = database('allowed', () => ({ data: [{ id: 'broken', venue_name: 42 }], count: 1, error: null }))
  assert.equal((await invalid.module.getReviewQueue('venues')).result.available, false)
})

test('queue pagination preserves source-grounded recurrence and distinguishes empty, out-of-range and failed pages', async () => {
  const row = { id: 'record', title: 'Regular programme', listing_type: 'activity', start_date: '2026-10-16', end_date: '2026-10-16', recurrence: 'recurring', schedule_text: 'Friday in term time', source_url: 'https://example.com/', event_url: 'https://example.com/detail', notes: 'private' }
  const test = database('allowed', () => ({ data: [row], count: 21, error: null }))
  const result = await test.module.getReviewQueue('activities', '2')
  assert.equal(result.result.value.total, 21)
  assert.equal(result.result.value.rows[0].schedule, 'Friday in term time')
  assert.equal(result.result.value.rows[0].recurrence, 'recurring')
  assert.equal(result.result.value.rows[0].start, '2026-10-16')
  assert.equal(JSON.stringify(result).includes('private'), false)
  assert.deepEqual(test.queries[0].range, [20, 39])
  assert.deepEqual(test.queries[0].orders, ['last_verified_at', 'id'])
  assert.deepEqual(test.queries[0].filters, [['is', 'venue_id', null], ['is', 'withdrawn_at', null], ['eq', 'listing_type', 'activity']])
  const empty = database('allowed', () => ({ data: [], count: 0, error: null }))
  assert.equal((await empty.module.getReviewQueue()).result.value.total, 0)
  const outside = database('allowed', () => ({ data: [], count: 21, error: null }))
  assert.equal((await outside.module.getReviewQueue('activities', '3')).result.available, true)
  assert.equal((await outside.module.getReviewQueue('activities', '1')).result.available, false)
  const failure = database('allowed', () => ({ data: [], count: null, error: { message: 'private' } }))
  assert.equal((await failure.module.getReviewQueue()).result.available, false)
})

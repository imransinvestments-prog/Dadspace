const assert = require('node:assert/strict')
const { test } = require('node:test')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, dependencies) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, process, Date, Intl, Response, URL, console, require: name => dependencies[name] ?? require(name) })
  return module.exports
}
function feeds(db) {
  const dependencies = { 'server-only': {}, './supabase': { getSupabase: () => db }, './dates': { londonToday: () => '2026-10-14', upcomingWeekend: () => ({ saturday: '2026-10-17', sunday: '2026-10-18' }) }, './distance': {}, './listing-distance': {}, './event-meta': {}, './activity-shared': { ACTIVITY_PAGE_SIZE: 24 } }
  return { events: load('lib/events.ts', dependencies), activities: load('lib/activities.ts', dependencies) }
}
function database(results) {
  let index = 0
  return { from: () => { const q = {}; for (const method of ['select', 'order', 'eq', 'or']) q[method] = () => q; q.range = async () => { const value = results[Math.min(index++, results.length - 1)]; if (value instanceof Error) throw value; return value }; return q } }
}
test('missing configuration and query/transport failures are unavailable for national and nearby listings', async () => {
  for (const db of [null, database([{ data: null, error: {} }]), database([{ data: null, error: null }]), database([new Error('transport')])]) {
    for (const point of [undefined, { lat: 51.5, lng: -0.1 }]) {
      const f = feeds(db)
      assert.equal((await f.events.fetchUpcomingEvents(point)).loadFailed, true)
      assert.equal((await f.activities.fetchActivityPage({ point })).loadFailed, true)
    }
  }
})
test('successful empty national results remain an honest empty state', async () => {
  const f = feeds(database([{ data: [], error: null, count: 0 }]))
  assert.equal((await f.events.fetchUpcomingEvents()).loadFailed, false)
  assert.equal((await f.activities.fetchActivityPage()).loadFailed, false)
})
test('failure after a full events page cannot publish a partial successful response', async () => {
  const f = feeds(database([{ data: Array.from({length:500}, () => ({})), error: null }, { data: null, error: {} }]))
  const result = await f.events.fetchUpcomingEvents()
  assert.equal(result.loadFailed, true)
  assert.equal(result.events.length, 0)
})
test('public directory APIs return 503 for unavailable supply and 200 for genuine empty supply', async () => {
  for (const loadFailed of [true, false]) {
    const events = load('app/api/events/route.ts', { '@/lib/events': { fetchUpcomingEvents: async () => ({ events: [], loadFailed }) }, '@/lib/distance': { parsePoint: () => null } })
    assert.equal((await events.GET(new Request('https://example.com/api/events'))).status, loadFailed ? 503 : 200)
    const activities = load('app/api/activities/route.ts', { 'next/server': { NextResponse: Response }, '@/lib/activities': { ACTIVITY_PAGE_SIZE: 24, fetchActivityPage: async () => ({ activities: [], loadFailed }) }, '@/lib/distance': { parsePoint: () => null } })
    assert.equal((await activities.GET(new Request('https://example.com/api/activities'))).status, loadFailed ? 503 : 200)
  }
})

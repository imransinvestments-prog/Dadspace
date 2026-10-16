const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, dependencies = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, URLSearchParams, URL, Request, Response, Date, Intl, require: name => {
    if (!(name in dependencies)) throw new Error(`Unexpected dependency ${name}`)
    return dependencies[name]
  } })
  return module.exports
}
const radius = load('lib/discovery-radius.ts')
const distance = load('lib/distance.ts')
const ids = rows => Array.from(rows, row => row.id)
const point = { lat: 51.48, lng: -3.18 } // Cardiff
const row = (id, miles, location = 'Cardiff') => ({ id, title: id, location, distance_miles: miles, start_date: '2026-10-17', family_relevance: 5 })
const rows = [row('inside', 6.2), row('boundary', 10 / 1.609344), row('outside', 6.22), row('old-cardiff-activity', 56), row('old-cardiff-event', 57), row('sale-89', 89), row('sale-128', 128), row('unknown', null), row('online', null, 'Online via Zoom')]

test('radius boundary is inclusive; Cardiff distant, unknown and online listings are not local', () => {
  assert.deepEqual(ids(radius.withinDiscoveryScope(rows)), ['inside', 'boundary'])
  assert.deepEqual(ids(radius.withinDiscoveryScope(rows, 10, 'unknown')), ['unknown'])
  assert.deepEqual(ids(radius.withinDiscoveryScope(rows, 10, 'online')), ['online'])
  assert.deepEqual(ids(radius.withinDiscoveryScope(rows, 100)), ['inside', 'boundary', 'outside', 'old-cardiff-activity', 'old-cardiff-event'])
  assert.equal(radius.withinDiscoveryScope([row('negative', -1), row('nan', NaN), row('infinite', Infinity)]).length, 0)
})

test('public contract defaults nearby to 10 km and rejects unsafe radius/scope combinations', () => {
  assert.equal(radius.parseDiscoveryRadius(new URLSearchParams()).radiusKm, 10)
  for (const value of ['', 'NaN', 'Infinity', '-1', '0', '101']) {
    assert.equal(radius.parseDiscoveryRadius(new URLSearchParams({ lat: '51', lng: '-3', radiusKm: value })), null)
  }
  assert.equal(radius.parseDiscoveryRadius(new URLSearchParams('radiusKm=10')), null)
  assert.equal(radius.parseDiscoveryRadius(new URLSearchParams('lat=51&lng=-3&scope=national')), null)
})

function feeds(data) {
  const db = { from: () => { const request = {}; for (const name of ['select', 'order', 'eq', 'or']) request[name] = () => request
    request.range = async (a, b) => ({ data: data.slice(a, b + 1), count: data.length, error: null }); return request } }
  const dependencies = { 'server-only': {}, './supabase': { getSupabase: () => db }, './activity-shared': { ACTIVITY_PAGE_SIZE: 24 }, './discovery-radius': radius, './distance': distance,
    './listing-distance': { withDistances: async mapped => mapped.map(item => ({ ...item, distance_miles: data.find(row => row.id === item.id).distance_miles })) },
    './dates': { londonToday: () => '2026-10-16', upcomingWeekend: () => ({ saturday: '2026-10-17', sunday: '2026-10-18' }) }, './event-meta': {} }
  return { activities: load('lib/activities.ts', dependencies), events: load('lib/events.ts', dependencies) }
}

test('activities filter before counting/paging and retain separate unknown/online discovery', async () => {
  const { activities } = feeds(rows)
  const first = await activities.fetchActivityPage({ point, limit: 1 })
  assert.deepEqual(ids(first.activities), ['inside']); assert.equal(first.total, 2); assert.equal(first.hasMore, true)
  const second = await activities.fetchActivityPage({ point, limit: 1, offset: 1 })
  assert.deepEqual(ids(second.activities), ['boundary']); assert.equal(second.hasMore, false)
  assert.deepEqual(ids((await activities.fetchActivityPage({ point, scope: 'unknown' })).activities), ['unknown'])
  assert.deepEqual(ids((await activities.fetchActivityPage({ point, scope: 'online' })).activities), ['online'])
  assert.equal((await activities.fetchActivityPage()).total, rows.length)
})

test('events bound local supply before explorer filters; national inventory remains available', async () => {
  const { events } = feeds(rows)
  assert.deepEqual(ids((await events.fetchUpcomingEvents(point)).events), ['inside', 'boundary'])
  assert.equal((await events.fetchUpcomingEvents()).events.length, rows.length)
  assert.deepEqual(ids((await events.fetchUpcomingEvents(point, 10, 'unknown')).events), ['unknown'])
  const empty = await feeds([row('distant', 57)]).events.fetchUpcomingEvents(point)
  assert.equal(empty.events.length, 0); assert.equal(empty.loadFailed, false)
})

test('both APIs reject invalid radius/location without querying supply and pass valid scope', async () => {
  for (const kind of ['activities', 'events']) {
    let calls = []
    const api = load(`app/api/${kind}/route.ts`, { 'next/server': { NextResponse: Response }, '@/lib/discovery-radius': radius, '@/lib/distance': distance,
      '@/lib/activities': { ACTIVITY_PAGE_SIZE: 24, fetchActivityPage: async options => { calls.push(options); return { activities: [] } } },
      '@/lib/events': { fetchUpcomingEvents: async (...args) => { calls.push(args); return { events: [] } } } })
    for (const query of ['lat=51&lng=-3&radiusKm=-1', 'lat=abc&lng=-3', 'scope=unknown', 'lat=51&lng=-3&scope=invalid']) {
      assert.equal((await api.GET(new Request(`https://example.com/api/${kind}?${query}`))).status, 400)
    }
    assert.equal(calls.length, 0)
    assert.equal((await api.GET(new Request(`https://example.com/api/${kind}?lat=51&lng=-3&radiusKm=25&scope=unknown`))).status, 200)
    assert.equal(kind === 'events' ? calls[0][1] : calls[0].radiusKm, 25)
    assert.equal(kind === 'events' ? calls[0][2] : calls[0].scope, 'unknown')
  }
})


test('homepage can retain its explicitly labelled 30-mile scope', async () => {
  const { events } = feeds([row('twenty-miles', 20), row('thirty-one-miles', 31)])
  assert.equal((await events.fetchUpcomingEvents(point)).events.length, 0)
  assert.deepEqual(ids((await events.fetchUpcomingEvents(point, 30 * 1.609344)).events), ['twenty-miles'])
})

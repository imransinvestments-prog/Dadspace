const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, dependencies = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, Request, Response, JSON, Number, console, require: name => {
    if (!(name in dependencies)) throw new Error(`Unexpected dependency ${name}`)
    return dependencies[name]
  } })
  return module.exports
}
const vitals = load('lib/web-vitals.ts')
const PHONE = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/131.0 Mobile Safari/537.36'
const LAPTOP = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'
const beacon = (extra = {}) => ({ name: 'LCP', value: 2412.5, rating: 'good', id: 'v5-1729-1', navigationType: 'navigate', route: '/', ...extra })

test('a phone LCP beacon becomes one row with no identifying fields', () => {
  assert.deepEqual({ ...vitals.parseVital(beacon(), PHONE) }, {
    metric: 'LCP', value: 2412.5, rating: 'good', metric_id: 'v5-1729-1', navigation_type: 'navigate', route: '/', device: 'mobile',
  })
  assert.equal(vitals.parseVital(beacon({ route: '/events/fireworks/' }), LAPTOP).route, '/events/fireworks')
  assert.equal(vitals.parseVital(beacon({ rating: 'excellent' }), LAPTOP).rating, null)
})

test('crawlers, lab tools and malformed or out-of-range reports are dropped', () => {
  for (const agent of [null, 'Googlebot/2.1', LAPTOP + ' Chrome-Lighthouse', 'HeadlessChrome/131']) {
    assert.equal(vitals.parseVital(beacon(), agent), null, String(agent))
  }
  for (const extra of [{ name: 'FID' }, { value: -1 }, { value: NaN }, { value: '2400' }, { value: 700000 },
    { name: 'CLS', value: 101 }, { id: '' }, { id: 'x'.repeat(101) }, { route: 'https://evil.example/' },
    { route: '/?postcode=W39LN' }, { route: '/a#b' }, { route: '/' + 'a'.repeat(200) }]) {
    assert.equal(vitals.parseVital(beacon(extra), PHONE), null, JSON.stringify(extra))
  }
  assert.equal(vitals.parseVital('LCP', PHONE), null)
})

function route(isProduction, db) {
  return load('app/api/vitals/route.ts', { '@/lib/supabase': { getSupabase: () => db }, '@/lib/seo': { isProduction }, '@/lib/web-vitals': vitals })
}
function fakeDb() {
  const calls = []
  return { calls, from: table => ({ upsert: (row, options) => { calls.push({ table, row, options }); return Promise.resolve({ error: null }) } }) }
}
const post = (body, agent = PHONE) => new Request('https://www.dad-space.co.uk/api/vitals', { method: 'POST', body, headers: { 'user-agent': agent } })

test('the endpoint stores production beacons once and answers every request with an empty 204', async () => {
  const db = fakeDb()
  const response = await route(true, db).POST(post(JSON.stringify(beacon())))
  assert.equal(response.status, 204)
  assert.equal(db.calls.length, 1)
  assert.equal(db.calls[0].table, 'web_vitals')
  assert.deepEqual({ ...db.calls[0].options }, { onConflict: 'metric_id', ignoreDuplicates: true })
  for (const body of ['not json', JSON.stringify(beacon({ name: 'FID' })), 'x'.repeat(2049)]) {
    assert.equal((await route(true, db).POST(post(body))).status, 204)
  }
  assert.equal(db.calls.length, 1)
})

test('preview and local traffic is never stored', async () => {
  const db = fakeDb()
  assert.equal((await route(false, db).POST(post(JSON.stringify(beacon())))).status, 204)
  assert.equal(db.calls.length, 0)
})

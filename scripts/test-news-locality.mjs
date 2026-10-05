import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const ts = require('typescript')
const root = path.resolve(import.meta.dirname, '..')
const cache = new Map()
// Exercise the real TS modules without adding a test runner dependency.
function load(file) {
  const full = path.join(root, file)
  if (cache.has(full)) return cache.get(full)
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(full, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
  }).outputText
  vm.runInNewContext(code, {
    module, exports: module.exports, process, console, URL, URLSearchParams, AbortSignal, Request, Response,
    fetch: (...args) => globalThis.fetch(...args),
    require: (name) => {
      if (name === 'next/server') return { NextResponse: { json: (body, init) => new Response(JSON.stringify(body), init) } }
      if (name.startsWith('@/')) return load(`${name.slice(2)}.ts`)
      if (name.startsWith('.')) {
        const local = path.resolve(path.dirname(full), name)
        return name.endsWith('.json') ? require(local) : load(`${path.relative(root, local)}.ts`)
      }
      return require(name)
    },
  }, { filename: full })
  cache.set(full, module.exports)
  return module.exports
}
const { newsLocationFilter, parseNewsLocation, fetchNews } = load('lib/news.ts')
const { newsArea, newsGeoRegion } = load('lib/news-geography.ts')
const location = { version: 2, region: 'england', geoRegion: 'east_of_england', adminArea: 'cambridgeshire', locality: 'cambridge' }

// Evaluate the filter expression independently against synthetic stories.
function split(text) {
  let depth = 0, start = 0
  const parts = []
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '(') depth++
    if (text[i] === ')') depth--
    if (text[i] === ',' && depth === 0) { parts.push(text.slice(start, i)); start = i + 1 }
  }
  parts.push(text.slice(start))
  return parts
}
function match(expr, row) {
  if (expr.startsWith('and(')) return split(expr.slice(4, -1)).every(part => match(part, row))
  const [column, op, value] = expr.split('.')
  if (op === 'is') return value === 'null' && row[column] == null
  assert.equal(op, 'eq')
  return row[column] === value
}
const filter = newsLocationFilter('england', location)
const cases = [
  [{ region: 'uk', geo_scope: 'nationwide' }, true],
  [{ region: 'england', geo_scope: 'nationwide' }, true],
  [{ region: 'england', geo_scope: null, locality: 'leeds' }, true],
  [{ region: 'scotland', geo_scope: null }, false],
  [{ region: 'england', geo_scope: 'regional', geo_region: 'east_of_england' }, true],
  [{ region: 'england', geo_scope: 'regional', geo_region: 'north_west' }, false],
  [{ region: 'england', geo_scope: 'local', locality: 'cambridge', admin_area: 'cambridgeshire' }, true],
  [{ region: 'england', geo_scope: 'local', locality: 'ely', admin_area: 'cambridgeshire' }, false],
  [{ region: 'england', geo_scope: 'local', locality: null, admin_area: 'cambridgeshire' }, true],
  [{ region: 'england', geo_scope: 'local', locality: null, admin_area: 'kent' }, false],
  [{ region: 'wales', geo_scope: 'local', locality: 'cambridge' }, false],
]
for (const [row, expected] of cases) assert.equal(split(filter).some(part => match(part, row)), expected, JSON.stringify(row))
assert.equal(newsLocationFilter('all', location), null)
assert.equal(newsLocationFilter('england', null), 'region.eq.uk,region.eq.england')
assert.equal(newsLocationFilter('scotland', location), 'region.eq.uk,region.eq.scotland')
for (const input of [null, [], {}, { ...location, version: 1 }, { ...location, locality: ['cambridge'] }, { ...location, locality: 'cambridge),region.eq.wales' }, { ...location, adminArea: 10 }, { ...location, locality: 'a'.repeat(101) }]) {
  assert.equal(parseNewsLocation(input), null)
}
assert.equal(newsArea('Glasgow City Council'), 'glasgow_city')
assert.equal(newsArea('Cambridge City Council'), 'cambridge')
assert.equal(newsArea('Bristol'), 'bristol_city_of')
assert.equal(newsArea('(pseudo) England (UA/MD/LB)'), null)
assert.equal(newsGeoRegion('Yorkshire and Humber'), 'yorkshire_and_the_humber')
assert.equal(newsGeoRegion('South Wales'), null)
assert.equal(parseNewsLocation({ ...location, locality: 'ballycastle', adminArea: 'made_up_county' }).locality, null)
assert.equal(parseNewsLocation({ ...location, region: 'wales' }).locality, null)

const originalFetch = globalThis.fetch
try {
  process.env.NEXT_PUBLIC_SUPABASE_URL = 'https://example.supabase.co'
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = 'public-test-key'
  let requested
  globalThis.fetch = async (url, options) => {
    requested = { url: new URL(url), options }
    return new Response('[]', { status: 200, headers: { 'Content-Type': 'application/json' } })
  }
  await fetchNews({ region: 'england', category: 'education', page: 1, location })
  assert.equal(requested.url.searchParams.get('or'), `(${filter})`)
  assert.equal(requested.url.searchParams.get('category'), 'eq.education')
  assert.equal(requested.url.searchParams.get('offset'), '20')
  assert.equal(requested.url.searchParams.get('limit'), '20')

  const { GET } = load('app/api/region/route.ts')
  for (const query of ['', 'lat=&lng=0', 'lat=1', 'lat=91&lng=0', 'lat=0&lng=NaN']) {
    assert.equal((await GET(new Request(`https://example.test/api/region?${query}`))).status, 400)
  }
  globalThis.fetch = async (url) => {
    assert.equal(new URL(url).searchParams.get('lat'), '52.20')
    assert.equal(new URL(url).searchParams.get('lon'), '0.12')
    return new Response(JSON.stringify({ result: [{ country: 'England', region: 'East of England', admin_county: 'Cambridgeshire', admin_district: 'Cambridge', parish: 'Cambridge, unparished area', admin_ward: 'Market' }] }))
  }
  const result = await (await GET(new Request('https://example.test/api/region?lat=52.2048&lng=0.1198'))).json()
  assert.deepEqual(result, location)
  globalThis.fetch = async () => new Response(JSON.stringify({ result: [{ country: 'Scotland', region: null, admin_county: '(pseudo) Scotland', admin_district: 'City of Edinburgh', admin_ward: 'Leith' }] }))
  const scotland = await (await GET(new Request('https://example.test/api/region?lat=55.95&lng=-3.19'))).json()
  assert.equal(scotland.locality, 'city_of_edinburgh')
  assert.equal(scotland.adminArea, 'city_of_edinburgh')
  assert.equal(scotland.geoRegion, null)
  globalThis.fetch = async () => { throw new Error('lookup failed') }
  assert.equal((await GET(new Request('https://example.test/api/region?lat=1&lng=1'))).status, 502)
} finally { globalThis.fetch = originalFetch }
console.log('News locality tests passed: geographic relevance, legacy fallback, specificity, input validation, API lookup, query/category/pagination.')

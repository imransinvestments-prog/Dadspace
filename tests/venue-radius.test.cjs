const { test, before, after } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
const { PGlite } = require('@electric-sql/pglite')

function load(file, dependencies = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, URLSearchParams, URL, Request, Response, require: name => {
    if (!(name in dependencies)) throw new Error(`Unexpected dependency ${name}`)
    return dependencies[name]
  } })
  return module.exports
}
let db
before(async () => {
  db = new PGlite()
  await db.exec(`create role anon; create role authenticated; create role service_role;
    create table public.venues(id text primary key, venue_name text, venue_label text, category text, fee text,
      public_visible boolean, latitude double precision, longitude double precision, town_city text, postcode text, address text, notes text);
    insert into venues
      select 'local-'||i, 'Local '||lpad(i::text,2,'0'), null, 'Park', case when i%2=0 then 'no' else 'yes' end,
        true, .001*(i+1), 0, 'Fixture town', null, null, 'private evidence'
      from generate_series(0,29) i;
    insert into venues values
      ('inside','Just inside',null,'Museum','no',true,degrees(9.999/6371),0,null,null,null,'private evidence'),
      ('outside','Just outside',null,'Museum','no',true,degrees(10.001/6371),0,null,null,null,null),
      ('far','Cardiff regression distance',null,'Museum','no',true,degrees(90.0/6371),0,null,null,null,null),
      ('unknown','Unknown coordinates',null,'Library','no',true,null,null,null,null,null,null),
      ('invalid','Invalid coordinates',null,'Library','no',true,200,0,null,null,null,null),
      ('hidden','Hidden park',null,'Park','no',false,0,0,null,null,null,null),
      ('nameless',' ',null,'Park','no',true,0,0,null,null,null,null);
    grant select on venues to service_role;`)
  await db.exec(fs.readFileSync('supabase/migrations/20261016135627_discovery_venue_radius.sql', 'utf8'))
})
after(async () => db?.close())

async function page(options = {}) {
  const o = { lat: 0, lng: 0, query: '', category: 'all', free: false, offset: 0, limit: 24, radius: 10, scope: 'local', ...options }
  const result = await db.query('select discovery_venue_page($1,$2,$3,$4,$5,$6,$7,$8,$9) as page', [o.lat,o.lng,o.query,o.category,o.free,o.offset,o.limit,o.radius,o.scope])
  return result.rows[0].page
}

test('real PostgreSQL filters radius before count/page and excludes hidden/nameless/unknown places', async () => {
  const first = await page(), second = await page({ offset: 24 })
  assert.equal(first.total, 31); assert.equal(first.rows.length, 24); assert.equal(second.rows.length, 7)
  const rows = [...first.rows, ...second.rows]
  assert.equal(new Set(rows.map(r => r.id)).size, first.total)
  assert(rows.some(r => r.id === 'inside'))
  for (const id of ['outside','far','unknown','invalid','hidden','nameless']) assert(!rows.some(r => r.id === id), id)
  assert(rows.every(r => r.distance_miles * 1.609344 <= 10))
})

test('radius, category, free and text filters count the same eligible set', async () => {
  assert.equal((await page({ category: 'museum' })).total, 1)
  assert.equal((await page({ free: true })).total, 16)
  assert.equal((await page({ query: 'Local 00', free: true })).total, 1)
  assert.equal((await page({ query: 'Local 01', free: true })).total, 0)
  const expanded = await page({ radius: 100, category: 'museum' })
  assert.equal(expanded.total, 3)
  assert.deepEqual(expanded.rows.map(r => r.id), ['inside','outside','far'])
  assert.equal((await page({ radius: .01 })).total, 0)
})

test('missing/invalid coordinates are separately discoverable and national inventory is preserved', async () => {
  const unknown = await page({ scope: 'unknown' })
  assert.equal(unknown.total, 2)
  assert(unknown.rows.every(r => r.distance_miles === null))
  assert.deepEqual(unknown.rows.map(r => r.id), ['invalid','unknown'])
  assert.equal((await page({ lat: null, lng: null })).total, 35)
})

test('SQL independently rejects malformed radius, scope and point inputs', async () => {
  for (const options of [{radius:0},{radius:-1},{radius:101},{radius:NaN},{radius:Infinity},{scope:'online'},{scope:null},{lat:91},{lng:181},{lat:null},{lat:null,lng:null,scope:'unknown'}]) {
    await assert.rejects(page(options), /Invalid radius or scope|Invalid location/)
  }
})

test('database function is invoker-only and executable only by the existing service role', async () => {
  const { rows } = await db.query(`select p.prosecdef,
    has_function_privilege('anon',p.oid,'execute') as anon,
    has_function_privilege('authenticated',p.oid,'execute') as authenticated,
    has_function_privilege('service_role',p.oid,'execute') as service
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='discovery_venue_page'`)
  assert.deepEqual(rows[0], { prosecdef: false, anon: false, authenticated: false, service: true })
})

test('venue API returns exact bounded pages through the SQL function without internal evidence', async () => {
  const radius = load('lib/discovery-radius.ts')
  const distance = load('lib/distance.ts')
  const { toVenue } = load('lib/venues.ts', { 'server-only': {} })
  let calls = 0
  const api = load('app/api/venues/route.ts', {
    '@/lib/discovery-radius': radius, '@/lib/distance': distance, '@/lib/venues': { toVenue },
    '@/lib/venue-discovery': { publicVenuePage: async () => ({venues:[],total:0,hasMore:false,loadFailed:false}) },
    '@/lib/supabase': { getSupabase: () => ({ rpc: async (name, args) => {
      assert.equal(name, 'discovery_venue_page'); calls++
      return {data:await page({lat:args.p_lat,lng:args.p_lng,query:args.p_query,category:args.p_category,free:args.p_free,offset:args.p_offset,limit:args.p_limit,radius:args.p_radius_km,scope:args.p_scope}),error:null}
    } }) },
  })
  const first = await (await api.GET(new Request('https://example.com/api/venues?lat=0&lng=0'))).json()
  assert.equal(first.total,31); assert.equal(first.hasMore,true); assert.equal(first.venues.length,24)
  assert(!('notes' in first.venues[0])); assert.equal(typeof first.venues[0].distance_miles,'number')
  const second = await (await api.GET(new Request('https://example.com/api/venues?lat=0&lng=0&offset=24'))).json()
  assert.equal(second.total,31); assert.equal(second.hasMore,false); assert.equal(second.venues.length,7)
  const unknown = await (await api.GET(new Request('https://example.com/api/venues?lat=0&lng=0&scope=unknown'))).json()
  assert.equal(unknown.total,2)
  assert(unknown.venues.every(v=>v.latitude===null&&v.longitude===null&&v.distance_miles===null))
  for (const query of ['lat=NaN&lng=0','lat=0&lng=0&radiusKm=101','scope=unknown','lat=0&lng=0&scope=online']) {
    assert.equal((await api.GET(new Request('https://example.com/api/venues?'+query))).status,400)
  }
  assert.equal(calls,3)
})

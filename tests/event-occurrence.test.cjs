const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, dependencies = {}) {
  const module = { exports: {} }
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText,
    { module, exports: module.exports, URL, Date, Intl, Response, process, require: name => dependencies[name] ?? require(name) })
  return module.exports
}
const dependencies = { 'server-only': {}, './supabase': {}, './dates': {}, './event-meta': {}, './distance': {}, './listing-distance': {}, './discovery-radius': {} }
const { dedupeEvents } = load('lib/events.ts', dependencies)
const rows = require('./fixtures/camp-occurrences-90.json')
const ids = values => Array.from(values, row => row.id).sort()
test('seven frozen source rows form four camp identities without mutation or order dependence', () => {
  const before = JSON.stringify(rows)
  const result = dedupeEvents(rows)
  assert.equal(result.length, 4)
  assert.equal(result.find(row => row.title === 'SportsStars Multi Sport Camp - Bromsgrove').venue_id, '81126502-e9eb-4aed-ad22-21e7d07f49ba')
  assert.ok(result.some(row => row.title === 'SportsStars Multi Sport Camp - Bromsgrove'))
  assert.ok(result.some(row => row.title === 'SportsStars Multi Sport Camp'))
  assert.ok(result.some(row => row.title === 'PandESports Football Camp'))
  assert.ok(result.some(row => row.title === 'PandESports Multi Activity Camp'))
  assert.deepEqual(ids(result), ids(dedupeEvents([...rows].reverse())))
  assert.deepEqual(ids(result), ids(dedupeEvents([...rows, ...rows.map(row => ({ ...row, id: row.id + '-repeat' }))])))
  assert.equal(JSON.stringify(rows), before)
})
test('conflicting or missing session, programme and source evidence never uses a camp alias', () => {
  const full = rows.find(row => row.title === 'PandESports Football Camp')
  const short = rows.find(row => row.title === 'PandESports' && row.location.includes('Trinity'))
  for (const change of [
    { start_date: '2026-10-28' }, { end_date: '2026-10-30' }, { end_date: null },
    { time_text: 'Afternoon' }, { time_text: null }, { title: 'PandESports Tennis Camp' },
    { age_range: '14 to 16 years' }, { cost_text: '£50' },
    { location: 'Another School, B98 8DS' }, { postcode: 'B98 1AA' },
    { event_url: 'https://pandesports.classforkids.io?programme=tennis' },
    { event_url: 'https://pandesports.classforkids.io?venueName=Other' },
    { event_url: 'https://pandesports.classforkids.io/camp/another' },
    { source_url: 'https://different.example' }, { is_holiday_camp: false },
  ]) assert.equal(dedupeEvents([full, { ...short, ...change }]).length, 2, JSON.stringify(change))
  assert.equal(dedupeEvents([{...full,venue_id:'one'}, {...short,venue_id:'two'}]).length, 2)
})
test('same listing URL cannot erase distinct times, date spans or programmes', () => {
  const a = { ...rows[0], is_holiday_camp: false, title: 'Family workshop', recurrence: null }
  for (const change of [{time_text:'09:00-10:00'}, {end_date:'2026-11-01'}, {title:'Family painting workshop'}, {start_date:a.start_date+'T14:00:00Z'}]) {
    assert.equal(dedupeEvents([a, {...a, id:'other', ...change}]).length, 2)
  }
  assert.equal(dedupeEvents([a, {...a, id:'same'}]).length, 1)
})
test('Home preserves different programmes after shared occurrence matching', async () => {
  const events = ['Football Camp', 'Tennis Camp'].map((title, i) => ({ ...rows[0], id:String(i), title, distance_miles:1 }))
  const route = load('app/api/home/nearby-week/route.ts', {
    'next/server': { NextResponse: Response }, '@/lib/supabase': {getSupabase:()=>null},
    '@/lib/distance': {parsePoint:()=>({lat:51,lng:0})},
    '@/lib/events': {fetchUpcomingEvents:async()=>({events,loadFailed:false,isSample:false})},
    '@/lib/listing-distance': {}, '@/lib/dates': {londonToday:()=> '2026-10-16',weekday:()=>5,addDays:()=> '2026-10-19'},
    '@/lib/home-selection': {},
  })
  const response = await route.GET({nextUrl:new URL('https://example.test?lat=51&lng=0')})
  assert.equal((await response.json()).events.length, 2)
})
test('public read path collapses a repeated import replay and retains all source rows', async () => {
  // Replay the existing stable source IDs twice; no collector or live writes.
  const stored = new Map()
  const db = {from:()=>{const q={}; for(const method of ['select','order']) q[method]=()=>q; q.range=async()=>({data:[...stored.values()],error:null}); return q}}
  const feed = load('lib/events.ts', {...dependencies, './supabase':{getSupabase:()=>db},
    './dates':{londonToday:()=> '2026-10-16',upcomingWeekend:()=>({saturday:'2026-10-17',sunday:'2026-10-18'})}})
  let previous
  for (let run=0; run<2; run++) {
    for (const row of rows) stored.set(row.id, {...row})
    const result = await feed.fetchUpcomingEvents()
    assert.equal(result.loadFailed, false)
    assert.equal(result.events.length, 4)
    assert.equal(stored.size, 7)
    if(previous) assert.deepEqual(ids(result.events),previous)
    previous=ids(result.events)
  }
})

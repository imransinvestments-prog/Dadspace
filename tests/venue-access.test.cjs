const { test } = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')

function load(file, deps = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, URL, require: name => {
    if (name === 'react/jsx-runtime') return require(name)
    if (!(name in deps)) throw new Error(`Unexpected dependency ${name}`)
    return deps[name]
  } })
  return module.exports
}
const { renderToStaticMarkup } = require('react-dom/server')
const access = load('components/venues/venue-access.tsx')
const { toVenue } = load('lib/venues.ts', { 'server-only': {} })
const icon = () => null
const common = {
  '@/components/venues/venue-photo': { VenuePhoto: () => null },
  '@/components/venues/venue-access': access,
  'lucide-react': Object.fromEntries(['Accessibility','Baby','Clock','Coffee','Dog','Globe','MapPin','Navigation','Phone','SquareParking','Dices','X'].map(k => [k,icon])),
  '@/lib/venue-meta': { FACILITY_LABELS: {}, categoryLabel: () => 'Playground' },
  '@/lib/utils': { cn: () => '' },
}
const spotlight = load('components/venues/venue-spotlight.tsx', common)
const { VenueCard } = load('components/venues/venue-card.tsx', { ...common,
  'next/link': { default: ({ children, ...props }) => require('react').createElement('a', props, children) },
  '@/lib/venue-slug': { venueSlug: v => v.id },
  '@/components/venues/venue-spotlight': spotlight,
})

test('reviewed access classes have distinct cautious wording without inventing price or permission', () => {
  for (const [tag, expected] of [['yes','Public access indicated'],[null,'Access information not supplied'],['customers','Customer access only'],['residents','Residents only'],['permit','Permit required'],['private','Private access'],['no','No public access']]) {
    const description = access.accessDescription(tag)
    assert(description.includes(expected), tag)
    assert(!/free entry|verified|booking required/i.test(description))
  }
  assert.equal(access.accessDescription(' CUSTOMERS '), access.accessDescription('customers'))
  assert.equal(access.accessDescription('unrecognised'), access.accessDescription(null))
})

test('public mapping retains normalized access independently of price without internal evidence', () => {
  const v = toVenue({ id: 'sample', venue_name: 'Splash Zone', access: ' CUSTOMERS ', fee: null, notes: 'private', review_reason: 'internal' })
  assert.equal(v.access, 'customers'); assert.equal(v.is_free, null); assert.equal(v.price_text, null)
  assert(!('notes' in v)); assert(!('review_reason' in v))
  assert.equal(toVenue({ venue_name: 'Midland Terrace Gardens', access: null }).access, null)
})

test('actual cards shared by directory/Home and surprise disclose conditions before navigation', () => {
  for (const tag of ['customers','residents','permit','yes',null]) {
    const venue = toVenue({ id:'sample', venue_name:'Reviewed playground', access:tag, town_city:'London', latitude:51.5, longitude:-.2 })
    for (const tree of [VenueCard({venue,distance:1}), spotlight.VenueSpotlight({venue,distance:1,rolling:false,onReroll(){},onClose(){}})]) {
      const html = renderToStaticMarkup(tree)
      assert(html.includes(access.accessDescription(tag).replaceAll('&','&amp;')))
      assert(html.indexOf('aria-label="Access information"') < html.indexOf('https://www.google.com/maps/'))
    }
  }
})

test('detail uses the same access notice before Directions and shared cards cover Home/directory', () => {
  const detail = fs.readFileSync('app/venues/[slug]/page.tsx','utf8')
  assert(detail.indexOf('<VenueAccess venue={v}') < detail.indexOf('href={directionsUrl(v)}'))
  for (const file of ['components/home/local-places.tsx','components/venues/venues-directory.tsx']) assert(fs.readFileSync(file,'utf8').includes('<VenueCard'))
  const projection = fs.readFileSync('lib/venue-discovery.ts','utf8').match(/VENUE_PUBLIC_COLUMNS = "([^"]+)"/)[1].split(',')
  assert(projection.includes('access')); assert(!projection.includes('review_reason'))
})

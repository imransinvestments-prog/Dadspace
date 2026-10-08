import assert from 'node:assert/strict'
import test from 'node:test'
import { venueSlug, venueIdFromSlug, browsePage } from '../lib/venue-slug.ts'
import { urlset, xmlEscape } from '../lib/sitemap-xml.ts'
import { isUnreleasedForumUrl } from '../scripts/sitemap-checks.mjs'
const id = '39197fb6-17ef-4bd9-95c5-51a0260d0216'
test('forum exclusion checks the route rather than legitimate venue names',()=>{
  assert(isUnreleasedForumUrl('https://www.dad-space.co.uk/forum'))
  assert(isUnreleasedForumUrl('https://www.dad-space.co.uk/forum/rooms'))
  assert(!isUnreleasedForumUrl('https://www.dad-space.co.uk/venues/forum-place-playground--'+id))
})
test('stable identity survives accents, punctuation and renamed venues',()=>{
  const old=venueSlug({id,name:'Café & Museum'}), updated=venueSlug({id,name:'New museum name'})
  assert.equal(old,`cafe-museum--${id}`)
  assert.notEqual(old,updated);assert.equal(venueIdFromSlug(old),id);assert.equal(venueIdFromSlug(updated),id)
  for(const input of ['unknown','abc--not-a-uuid',`museum--${id}/extra`])assert.equal(venueIdFromSlug(input),null)
})
test('browse pagination rejects malformed and unbounded input',()=>{
  assert.equal(browsePage(undefined),1);assert.equal(browsePage('2'),2)
  for(const v of ['0','-1','1.2','NaN','10000',['1','2']])assert.equal(browsePage(v),null)
})
test('sitemaps escape query strings and enforce protocol limits',()=>{
  assert.equal(xmlEscape('a&b<"'), 'a&amp;b&lt;&quot;')
  const xml=urlset([{url:'https://example.com/?a=1&b=2',lastModified:new Date('2026-10-08T00:00:00Z')}])
  assert(xml.includes('&amp;b=2'));assert(xml.includes('<lastmod>2026-10-08T00:00:00.000Z</lastmod>'))
  assert.throws(()=>urlset(Array.from({length:50001},()=>({url:'https://example.com'}))),/URL limit/)
})

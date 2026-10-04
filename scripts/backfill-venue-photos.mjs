import { createClient } from '@supabase/supabase-js'
import { mkdir, appendFile } from 'node:fs/promises'
import { dirname } from 'node:path'
import { googleApiKey, placesJson, PHOTO_MARKER, PlacesError } from '../lib/google-venue-photos.mjs'
import { searchableVenue, matchVenue } from '../lib/google-venue-match.mjs'

import { pathToFileURL } from 'node:url'

export async function runBackfill({db,apiKey,limit=100,maxCalls=100,apply=false,report='outputs/venue-google-photos.jsonl',after='',fetcher=fetch,sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms))}) {
if (![limit,maxCalls].every(n => Number.isSafeInteger(n) && n > 0)) throw new Error('limit and max-api-calls must be positive integers')
if (after && !/^[a-f0-9-]{36}$/i.test(after)) throw new Error('after must be a venue UUID from the report')
await mkdir(dirname(report),{recursive:true})
let cursor = after, scanned = 0, calls = 0, updated = 0, matched = 0, stopped = false
const fields = 'places.id,places.displayName,places.location,places.addressComponents,places.businessStatus,places.photos'
while (scanned < limit && calls < maxCalls) {
  let query = db.from('venues').select('id,venue_name,venue_label,category,address,address_line_1,address_line_2,town_city,postcode,latitude,longitude,image_url').is('image_url',null).order('id').limit(Math.min(500,limit-scanned))
  if (cursor) query = query.gt('id',cursor)
  const {data,error} = await query
  if (error) throw new Error(`Database read: ${error.message}`)
  if (!data?.length) break
  for (const row of data) {
    if (calls >= maxCalls) break
    let result = {status:'insufficient_identity'}
    if (searchableVenue(row)) {
      const textQuery = [...new Set([row.venue_name || row.venue_label,row.address || [row.address_line_1,row.address_line_2].filter(Boolean).join(', '),row.town_city,row.postcode,'United Kingdom'].filter(Boolean))].join(', ')
      calls++
      try {
        const response = await placesJson('places:searchText',{apiKey,fields,fetcher,body:{textQuery,regionCode:'GB',languageCode:'en',pageSize:5}})
        result = matchVenue(row,response.places || [])
        if (result.status === 'matched' && !response.places.find(p=>p.id===result.placeId)?.photos?.length) result = {status:'no_photo'}
      } catch (error) {
        // Stop on credential/quota errors. Leave this row available for retry.
        if (error instanceof PlacesError && [401,403,429].includes(error.status)) {
          console.error(`${error.message}; stopping. Resume with --after=${cursor || '(omit)'}`)
          stopped = true
          break
        }
        // Fail without advancing cursor so transient failures can be retried.
        throw error
      }
      await sleep(250)
    }
    if (result.status === 'matched') {
      matched++
      if (apply) {
        const patch = {
          image_url: `${PHOTO_MARKER}${result.placeId}`,
          image_source_url: `https://www.google.com/maps/search/?api=1&query=venue&query_place_id=${result.placeId}`,
          image_attribution: 'Google Maps', image_license: 'Google Maps Platform',
          image_license_url: 'https://cloud.google.com/maps-platform/terms/',
          image_title: null, image_credit: null,
          image_match_method: 'google_places_verified_location',image_updated_at: new Date().toISOString(),
        }
        const {data:saved,error:writeError} = await db.from('venues').update(patch).eq('id',row.id).is('image_url',null).select('id')
        if (writeError) throw new Error(`Database update: ${writeError.message}`)
        result.status = saved?.length ? 'updated' : 'already_has_photo'
        if (saved?.length) updated++
      }
    }
    cursor=row.id;scanned++
    // Persist only our IDs and decisions, not Google names/photos/API content.
    await appendFile(report,JSON.stringify({venueId:row.id,status:result.status,...(result.placeId ? {placeId:result.placeId} : {})})+'\n')
    if (scanned%50===0) console.log(JSON.stringify({scanned,calls,matched,updated,cursor}))
  }
  if (stopped) break
}
return {dryRun:!apply,scanned,calls,matched,updated,resumeAfter:cursor,stopped,report}
}

async function main() {
const args = process.argv.slice(2)
const option = (name, fallback) => args.find(a => a.startsWith(`--${name}=`))?.slice(name.length + 3) ?? fallback
const limit = Number(option('limit','100'))
const maxCalls = Number(option('max-api-calls','100'))
const apply = args.includes('--apply')
const report = option('report','outputs/venue-google-photos.jsonl')
const after = option('after','')
if (![limit,maxCalls].every(n => Number.isSafeInteger(n) && n > 0)) throw new Error('limit and max-api-calls must be positive integers')
if (after && !/^[a-f0-9-]{36}$/i.test(after)) throw new Error('after must be a venue UUID from the report')
const apiKey = googleApiKey()
const url = process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL || process.env.SUPABASE_URL
const key = process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_KEY
if (!apiKey || !url || !key) throw new Error('Configure GOOGLE_PLACES_API_KEY, NEXT_PUBLIC_DADSPACE_SUPABASE_URL and DADSPACE_SUPABASE_SERVICE_ROLE_KEY in a private server environment')
const db = createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}})

const result=await runBackfill({db,apiKey,limit,maxCalls,apply,report,after})
console.log(JSON.stringify(result))
if (result.stopped) process.exitCode=1
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main().catch(error=>{console.error(error.message);process.exitCode=1})

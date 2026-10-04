import assert from 'node:assert/strict'
import { matchVenue, linkedPlaceId, venueSearchBody, searchableVenue } from '../lib/google-venue-match.mjs'
import { fetchVenuePhoto, googlePlaceId, safeGoogleUrl, PlacesError } from '../lib/google-venue-photos.mjs'
const id = 'ChIJvalidPlaceId123'
const venue = {venue_name:'Jump Factory',postcode:'M1 1AA',latitude:53.48,longitude:-2.24}
const place = {id,displayName:{text:'Jump Factory Manchester'},location:{latitude:53.4801,longitude:-2.24},addressComponents:[{types:['country'],shortText:'GB'},{types:['postal_code'],longText:'M1 1AA'}]}
assert.equal(matchVenue(venue,[place]).status,'matched')
assert.equal(matchVenue(venue,[{...place,location:{latitude:51.5,longitude:-.1}}]).status,'no_match')
assert.equal(matchVenue(venue,[place,{...place,id:'otherPlaceId'}]).status,'ambiguous')
assert.equal(matchVenue({...venue,latitude:null,longitude:null},[place]).status,'matched')
assert.equal(matchVenue({...venue,postcode:'M2 2BB',latitude:null,longitude:null},[place]).status,'no_match')
assert.equal(matchVenue(venue,[{...place,businessStatus:'CLOSED_PERMANENTLY'}]).status,'no_match')
assert.equal(matchVenue(venue,[{...place,displayName:{text:'Other Business'}}]).status,'no_match')
assert.equal(searchableVenue({...venue,category:'Children’s playground'}),false)
assert.equal(searchableVenue({...venue,category:'play_ground'}),false)
assert.equal(searchableVenue({...venue,image_url:'existing.jpg'}),false)
assert.equal(matchVenue({...venue,category:'Playground'},[place]).status,'excluded_playground')
assert.deepEqual(venueSearchBody(venue).locationBias.circle.center,{latitude:53.48,longitude:-2.24})
assert.equal(linkedPlaceId({...venue,website:`https://www.google.com/maps/search/?api=1&query_place_id=${id}`}),id)
assert.equal(linkedPlaceId({...venue,website:`https://evil.example/maps/?query_place_id=${id}`}),null)
assert.equal(searchableVenue({...venue,venue_name:null,website:`https://www.google.com/maps/?query_place_id=${id}`}),true)
const branch={...venue,website:'https://www.jumpfactory.co.uk/locations/manchester/'}
const renamed={...place,displayName:{text:'Renamed Adventure Centre'},websiteUri:'https://jumpfactory.co.uk/locations/manchester'}
assert.equal(matchVenue(branch,[renamed]).method,'website_location')
assert.equal(matchVenue(branch,[{...renamed,websiteUri:'https://jumpfactory.co.uk/locations/leeds'}]).status,'no_match')
assert.equal(matchVenue({...venue,website:'https://jumpfactory.co.uk'},[{...renamed,websiteUri:'https://jumpfactory.co.uk'}]).status,'no_match')
assert.equal(matchVenue(branch,[{...renamed,location:{latitude:51.5,longitude:-.1}}]).status,'no_match')
assert.equal(matchVenue({...venue,website:`https://www.google.com/maps/?q=place_id:${id}`},[renamed]).method,'linked_place_id_location')
assert.equal(googlePlaceId(`google-places:${id}`),id)
assert.equal(googlePlaceId('google-places:../attack'),null)
assert.equal(safeGoogleUrl('https://googleusercontent.com.evil.example/image',true),null)
assert.equal(safeGoogleUrl('javascript:alert(1)'),null)
const calls=[]
const fetcher=async (url,options) => {
  calls.push({url,options})
  return {ok:true,json:async()=> calls.length===1 ? {photos:[{name:`places/${id}/photos/freshName`,googleMapsUri:'https://www.google.com/maps/photo/test',authorAttributions:[{displayName:'Photographer',uri:'//maps.google.com/maps/contrib/123',photoUri:'//lh3.googleusercontent.com/avatar'}]}]} : {photoUri:'https://lh3.googleusercontent.com/photo'}}
}
const photo=await fetchVenuePhoto(id,'test-secret',fetcher)
assert.equal(photo.authors[0].name,'Photographer')
assert.equal(photo.authors[0].uri,'https://maps.google.com/maps/contrib/123')
assert.equal(photo.sourceUrl,'https://www.google.com/maps/photo/test')
assert.equal(calls.length,2)
assert.ok(calls.every(c=>c.options.cache==='no-store' && !c.url.includes('test-secret')))
assert.equal(await fetchVenuePhoto('invalid/path','key',fetcher),null)
await assert.rejects(()=>fetchVenuePhoto(id,'key',async()=>({ok:false,status:429})),PlacesError)
await assert.rejects(()=>fetchVenuePhoto(id,'test-secret',async()=>({ok:false,status:400,json:async()=>({error:{message:'Invalid credential test-secret'}})})),error=>error.message.includes('[redacted]') && !error.message.includes('test-secret'))
console.log('Google venue photo tests passed: location/name matching, ambiguous branches, safe URLs, fresh photo references and attribution.')

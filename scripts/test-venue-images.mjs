import assert from 'node:assert/strict'
import { categoryImage, venueImage, venuePhotoUrl } from '../lib/venue-meta.ts'

const photo = {
  category: 'museum',
  image_url: 'https://thumb.wikimedia.org/wikipedia/commons/thumb/example.jpg',
  image_source_url: 'https://commons.wikimedia.org/wiki/File:Example.jpg',
  image_attribution: 'Example Photographer',
  image_license: 'CC BY-SA 4.0',
  image_license_url: 'https://creativecommons.org/licenses/by-sa/4.0/',
}
assert.equal(venuePhotoUrl(photo), photo.image_url)
const stored = 'https://ebebkbrdqmceckmhlcpw.supabase.co/storage/v1/object/public/venue-images/12345678-1234-1234-1234-123456789abc/0123456789abcdef.webp'
assert.equal(venuePhotoUrl({ ...photo, image_url: stored }), stored)
assert.equal(venuePhotoUrl({ ...photo, image_url: stored.replace('venue-images', 'avatars') }), null)
assert.equal(venuePhotoUrl({ ...photo, image_url: stored.replace('ebebkbrdqmceckmhlcpw', 'another-project') }), null)
assert.equal(venuePhotoUrl({ ...photo, image_url: stored.replace('https://', 'https://user:password@') }), null)
assert.equal(venuePhotoUrl({ ...photo, image_url: stored, image_attribution: null }), null)
assert.equal(venueImage({ ...photo, image_attribution: null }), categoryImage('museum'))
assert.equal(venuePhotoUrl({ ...photo, image_source_url: 'javascript:alert(1)' }), null)
assert.equal(venuePhotoUrl({ ...photo, image_url: 'https://thumb.wikimedia.org.evil.example/image.jpg' }), null)
assert.equal(venuePhotoUrl({ ...photo, image_license_url: 'https://example.com/license' }), null)
assert.equal(categoryImage('theme_park'), '/images/venues/theme-park.png')
assert.equal(categoryImage('water_park'), '/images/venues/water-park.png')
assert.equal(categoryImage('children’s_playground'), '/images/venues/playground.png')
assert.equal(venueImage({ category: null, image_url: null }), '/images/event-outdoor.png')
console.log('Venue image tests passed: credit requirements, safe source URLs, category fallbacks and park categories.')

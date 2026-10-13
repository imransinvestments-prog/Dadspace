import assert from 'node:assert/strict'
import { originalActivityDescription } from '../lib/activity-copy.ts'

const base = { id: 'review', title: 'Stay & Play', venue_name: 'Tweedale', description: null }
const summary = description => originalActivityDescription({ ...base, description })
assert.match(summary('Our Best Start Family Hubs services are restricted to those living in the London Borough of Sutton only.'), /Sutton residents only/)
assert.doesNotMatch(summary('Open to all families.'), /residents only/)
assert.match(summary('Please book a ticket for each child and adult wanting to attend. Children must be accompanied by a responsible adult throughout. Please log in with your library credentials to reserve your place at this event.'), /each child and adult/)
assert.match(summary('No booking necessary, spots will be allocated on a first come first served basis.'), /first come, first served/)
assert.doesNotMatch(summary('No booking necessary, spots will be allocated on a first come first served basis.'), /Library credentials/)
assert.match(summary('Please only book a ticket for the child/children you are bringing, adults do not require a ticket.'), /adults do not need a ticket/)
assert.doesNotMatch(summary('Please book a ticket for each child attending.'), /adults do not need a ticket/)
assert.doesNotMatch(summary(null), /tickets|residents|credentials/)
assert.doesNotMatch(summary('Amazing best ever adventures!'), /Amazing|best ever/)
console.log('Activity attendance facts preserved without copying promotional descriptions.')


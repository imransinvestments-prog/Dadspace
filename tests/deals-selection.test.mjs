import test from "node:test"
import assert from "node:assert/strict"
import { eligibleDeal, selectDeals } from "../lib/deals-selection.ts"

const now = Date.parse("2026-10-05T12:00:00Z")
const row = (changes = {}) => ({ id: 1, title: "Baby cot now £150 was £200", description: "UK delivery £5", retailer: "Shop A", price: 150, was_price: 200, discount_pct: 25, image_url: null, display_group: "Nursery, Beds & Sleep", link: "https://example.com/cot?variant=blue", posted_at: null, last_seen: "2026-10-05T11:00:00Z", expires_at: null, relevance: 4, audience_evidence: "Baby cot", classified_by: "quality-v1:source-page:rules", status: "live", ...changes })

test("supported fresh offer eligible", () => assert.equal(eligibleDeal(row(), now), true))
test("legacy, unsupported, stale and unsafe records excluded", () => {
  for (const changes of [{ classified_by: "rules" }, { was_price: null }, { discount_pct: 99 }, { relevance: 2 }, { audience_evidence: null }, { status: "review" }, { last_seen: "2026-10-01T00:00:00Z" }, { last_seen: "bad" }, { last_seen: "2026-10-06T00:00:00Z" }, { link: "javascript:alert(1)" }, { link: "https://user:secret@example.com" }, { expires_at: "2026-10-05T12:00:00Z" }, { expires_at: "bad" }]) {
    assert.equal(eligibleDeal(row(changes), now), false, JSON.stringify(changes))
  }
})
test("absolute savings accepted; weak savings rejected", () => {
  assert.equal(eligibleDeal(row({ price: 250, was_price: 300, discount_pct: 16.7 }), now), true)
  assert.equal(eligibleDeal(row({ price: 9.9, was_price: 10, discount_pct: 1 }), now), false)
})
test("nonpercentage family benefits require conditions", () => {
  const offer = row({ title: "Kids eat free", description: "With an adult meal, under 12s only", price: null, was_price: null, discount_pct: null })
  assert.equal(eligibleDeal(offer, now), true)
  assert.equal(eligibleDeal({ ...offer, description: null }, now), false)
})
test("retailer and category diversity avoids repeated baby offers", () => {
  const rows = [row(), row({ id: 2, link: "https://example.com/b" }), row({ id: 3, link: "https://example.com/c", retailer: "Shop B", display_group: "Toys, Play & Outdoors" })]
  assert.deepEqual(selectDeals(rows, 3, now).map((x) => x.id), [1, 3, 2])
})
test("homepage first item matches deals first item, with deterministic ranking", () => {
  const rows = [row({ id: 2, link: "https://example.com/b" }), row()]
  assert.deepEqual(selectDeals(rows, 1, now), selectDeals(rows, 60, now).slice(0, 1))
  assert.deepEqual(selectDeals([...rows].reverse(), 60, now), selectDeals(rows, 60, now))
})
test("duplicate redemption links appear once", () => assert.equal(selectDeals([row(), row({ id: 2 })], 60, now).length, 1))
test("failure and honest empty pool stay empty", () => assert.deepEqual(selectDeals([], 60, now), []))


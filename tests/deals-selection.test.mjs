import test from "node:test"
import assert from "node:assert/strict"
import { eligibleDeal, selectDeals, dealItemKey } from "../lib/deals-selection.ts"

const now = Date.parse("2026-10-05T12:00:00Z")

test("canonical equivalence collapses wipes without merging other taxonomy items", () => {
  const rows = [row({ id: 1, title: "Brand A wipes", item_id: 8 }), row({ id: 2, title: "Reusable cloth wipes", item_id: 9, equivalent_item_id: 8, link: "https://example.com/other" }), row({ id: 3, title: "Different nursery item", item_id: 40, link: "https://example.com/third" })]
  assert.deepEqual(selectDeals(rows, 100, now).map(r => r.id).sort(), [1, 3])
})

test("breakfast offers accept explicit under-16 eligibility without a guessed percentage", () => {
  assert.equal(eligibleDeal(row({ title: "Kids eat free breakfast", description: "Two children under 16 with a full adult breakfast", price: null, was_price: null, discount_pct: null }), now), true)
})
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
  const rows = [row(), row({ id: 2, title: "Baby wipes", link: "https://example.com/b" }), row({ id: 3, title: "Kids scooter", link: "https://example.com/c", retailer: "Shop B", display_group: "Toys, Play & Outdoors" })]
  assert.deepEqual(selectDeals(rows, 3, now).map((x) => x.id), [1, 3, 2])
})
test("homepage first item matches deals first item, with deterministic ranking", () => {
  const rows = [row({ id: 2, link: "https://example.com/b" }), row()]
  assert.deepEqual(selectDeals(rows, 1, now), selectDeals(rows, 60, now).slice(0, 1))
  assert.deepEqual(selectDeals([...rows].reverse(), 60, now), selectDeals(rows, 60, now))
})
test("duplicate redemption links appear once", () => assert.equal(selectDeals([row(), row({ id: 2 })], 60, now).length, 1))
test("failure and honest empty pool stay empty", () => assert.deepEqual(selectDeals([], 60, now), []))

test("only the strongest wipe offer survives across brands, packs and retailers", () => {
  const rows = [row({ id: 1, title: "Pampers Sensitive Baby Wipes 1080 wipes", matched_item: "Baby wipes" }),
    row({ id: 2, title: "WaterWipes newborn 6 pack", retailer: "Shop B", link: "https://example.com/water", price: 140, discount_pct: 30 }),
    row({ id: 3, title: "Huggies plastic free baby wipes 12 x 60", retailer: "Shop C", link: "https://example.com/huggies" })]
  assert.deepEqual(selectDeals(rows, 100, now).map((item) => item.id), [2])
  assert.deepEqual(selectDeals([...rows].reverse(), 100, now).map((item) => item.id), [2])
})

test("ineligible strongest item cannot hide an eligible alternative", () => {
  assert.deepEqual(selectDeals([row({ id: 1, title: "Baby wipes", expires_at: "2026-10-04T00:00:00Z", relevance: 5 }), row({ id: 2, title: "WaterWipes", link: "https://example.com/wipes" })], 100, now).map((item) => item.id), [2])
})

test("nappies, bins, refills and cream remain distinct despite wrong legacy matches", () => {
  const rows = ["Pampers nappies", "Tommee Tippee Nappy Bin", "Nappy Bin Refill Cassettes", "Sudocrem Nappy Rash Cream"].map((title, index) => row({ id: index + 1, title, matched_item: "Disposable diapers", link: `https://example.com/${index}` }))
  assert.equal(new Set(rows.map(dealItemKey)).size, 4)
  assert.equal(selectDeals(rows, 100, now).length, 4)
})

test("missing item labels do not collapse an entire category", () => {
  const rows = [row({ title: "Kids dinosaur puzzle" }), row({ id: 2, title: "Children's painting set", link: "https://example.com/painting" })]
  assert.equal(selectDeals(rows, 100, now).length, 2)
})

test("family benefits from different venues remain distinct", () => {
  const rows = [row({ title: "Kids eat free", description: "With an adult meal", retailer: "Cafe A" }), row({ id: 2, title: "Kids eat free", description: "With an adult meal", retailer: "Cafe B", link: "https://example.com/cafe-b" })]
  assert.equal(selectDeals(rows, 100, now).length, 2)
})


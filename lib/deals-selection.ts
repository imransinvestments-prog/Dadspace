export type LiveDeal = {
  id: number | string
  title: string
  description: string | null
  retailer: string | null
  price: number | null
  was_price: number | null
  discount_pct: number | null
  image_url: string | null
  display_group: string | null
  link: string
  posted_at: string | null
  last_seen: string | null
  expires_at: string | null
  relevance: number | null
  audience_evidence: string | null
  classified_by: string | null
  status: string
}

export function familyBenefit(text: string) {
  const benefit = text.match(/\b(?:kids?|children)\s+(?:eat|go)\s+free\b|\b2\s+for\s+1\s+(?:family\s+)?(?:tickets|admission)\b/i)
  const terms = /\b(?:with (?:a |an )?(?:paying )?adult|per (?:paying )?adult|aged? \d|under \d|adult (?:meal|ticket|admission)|code\s+[a-z0-9]+)\b/i.test(text)
  return benefit && terms ? benefit[0] : null
}

export function dealBenefit(deal: LiveDeal) {
  return familyBenefit(`${deal.title} ${deal.description ?? ""}`)
}

export function eligibleDeal(deal: LiveDeal, now = Date.now()) {
  const seen = Date.parse(deal.last_seen ?? "")
  const expiry = deal.expires_at ? Date.parse(deal.expires_at) : null
  if (deal.status !== "live" || !/^quality-v1:source-(?:api|page):/.test(deal.classified_by ?? "") ||
      !deal.audience_evidence || Number(deal.relevance) < 3 ||
      !Number.isFinite(seen) || seen > now || now - seen > 72 * 3600000 ||
      (expiry !== null && (!Number.isFinite(expiry) || expiry <= now))) return false
  try {
    const url = new URL(deal.link)
    if (!["https:", "http:"].includes(url.protocol) || url.username || url.password) return false
  } catch { return false }
  if (dealBenefit(deal)) return true
  const price = deal.price == null ? NaN : Number(deal.price)
  const was = deal.was_price == null ? NaN : Number(deal.was_price)
  const pct = was > price && price >= 0 ? (was - price) / was * 100 : 0
  if (!Number.isFinite(price) || !Number.isFinite(was) || !Number.isFinite(Number(deal.discount_pct)) ||
      deal.discount_pct == null || Math.abs(pct - Number(deal.discount_pct)) > 0.2) return false
  return (was - price >= 10 && pct >= 10) || (was - price >= 1 && pct >= 20)
}

function score(deal: LiveDeal, now: number) {
  const savings = Math.max(0, Number(deal.was_price) - Number(deal.price))
  const freshness = Math.max(0, 1 - (now - Date.parse(deal.last_seen!)) / (72 * 3600000))
  return Number(deal.relevance) * 10 + freshness * 10 +
    (dealBenefit(deal) ? 15 : Math.min(savings, 50) / 5 + Math.min(Number(deal.discount_pct), 50) / 5)
}

/** One eligible pool for both /deals and the homepage; diversity affects order only. */
export function selectDeals(rows: LiveDeal[], count = 100, now = Date.now()) {
  const remaining = rows.filter((row) => eligibleDeal(row, now))
  const selected: LiveDeal[] = []
  const merchants = new Map<string, number>()
  const groups = new Map<string, number>()
  while (remaining.length && selected.length < count) {
    const adjusted = (row: LiveDeal) => score(row, now) -
      (merchants.get((row.retailer ?? "").toLowerCase()) ?? 0) * 12 -
      (groups.get(row.display_group ?? "") ?? 0) * 6
    remaining.sort((a, b) => adjusted(b) - adjusted(a) || String(a.id).localeCompare(String(b.id)))
    const next = remaining.shift()!
    if (selected.some((row) => row.link === next.link)) continue
    selected.push(next)
    const merchant = (next.retailer ?? "").toLowerCase()
    merchants.set(merchant, (merchants.get(merchant) ?? 0) + 1)
    const group = next.display_group ?? ""
    groups.set(group, (groups.get(group) ?? 0) + 1)
  }
  return selected
}


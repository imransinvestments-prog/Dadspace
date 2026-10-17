export const DEAL_CHECK_LABELS = {
  useful: "Useful and worthwhile for a family?",
  accurate: "Description, price and comparison basis accurate?",
  available: "Available and not expired at the time you checked?",
  destination: "Exact redemption link works for this offer?",
  terms: "Codes, conditions, delivery and geography clear?",
  savings: "Savings supported, or clearly disclosed as merchant-advertised?",
} as const
export type DealChecks = Record<keyof typeof DEAL_CHECK_LABELS, string>
export function validDealChecks(value: unknown): value is DealChecks {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false
  const row = value as Record<string, unknown>
  return Object.keys(DEAL_CHECK_LABELS).every(key => ["yes", "no", "unknown"].includes(String(row[key])))
}

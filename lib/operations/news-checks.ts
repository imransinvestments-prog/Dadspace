export const NEWS_CORE_KEYS = ["relevance", "attribution", "destination", "geography"] as const
export const NEWS_EXTRA_KEYS = ["summary", "date", "sensitiveLabel", "homepagePick"] as const
export const NEWS_CHECK_LABELS = {
  relevance: "Useful for dads/families in its intended area?",
  attribution: "Correct publisher attribution?",
  destination: "Does the article link open the correct destination?",
  geography: "Does the stored geographic targeting match the article?",
  summary: "Summary — accurate, clear and faithful to the article?",
  date: "Date — publication date and freshness presented correctly?",
  sensitiveLabel: "Sensitive label — handling appropriate, including no warning where none is needed?",
  homepagePick: "Homepage pick — presentation or selection appropriate where applicable?",
} as const
export type NewsChecks = Record<(typeof NEWS_CORE_KEYS)[number], string> & Partial<Record<(typeof NEWS_EXTRA_KEYS)[number], string>>
export const UNKNOWN_NEWS_CHECKS: NewsChecks = Object.fromEntries([...NEWS_CORE_KEYS,...NEWS_EXTRA_KEYS].map(key=>[key,"unknown"])) as NewsChecks
export function validNewsChecks(value: unknown): value is NewsChecks {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false
  const row=value as Record<string,unknown>
  return NEWS_CORE_KEYS.every(key=>["yes","no","unknown"].includes(String(row[key]))) && NEWS_EXTRA_KEYS.every(key=>row[key]===undefined || ["yes","no","unknown"].includes(String(row[key])))
}

import "server-only"
import { createHmac, timingSafeEqual, randomUUID } from "node:crypto"

export const REVIEW_ACTIONS = ["approve", "hide", "merge", "link", "rollback"] as const
export type ReviewAction = typeof REVIEW_ACTIONS[number]
export type ReviewIntent = { action: ReviewAction; record: string; target: string | null; reason: string }
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
export const validId = (value: unknown): value is string => typeof value === "string" && uuid.test(value)
export function reviewIntent(action: unknown, record: unknown, target: unknown, reason: unknown): ReviewIntent | null {
  if (!REVIEW_ACTIONS.includes(action as ReviewAction) || !validId(record) || typeof reason !== "string" ||
    reason.trim().length < 10 || reason.trim().length > 1000) return null
  const needsTarget = action === "merge" || action === "link"
  if (needsTarget && (!validId(target) || target === record)) return null
  if (!needsTarget && target) return null
  return { action: action as ReviewAction, record, target: needsTarget ? String(target) : null, reason: reason.trim() }
}
export type ReviewToken = ReviewIntent & { actor: string; fingerprint: string; request: string; expires: number }
function signature(value: string, secret: string) {
  return createHmac("sha256", secret).update("dadspace-review-v1:" + value).digest("base64url")
}
export function signReview(intent: ReviewIntent, actor: string, fingerprint: string, secret: string, now = Date.now()) {
  const payload: ReviewToken = { ...intent, actor, fingerprint, request: randomUUID(), expires: now + 15 * 60 * 1000 }
  const value = Buffer.from(JSON.stringify(payload)).toString("base64url")
  return `${value}.${signature(value, secret)}`
}
export function verifyReview(token: unknown, actor: string, secret: string, now = Date.now()): ReviewToken | null {
  if (typeof token !== "string" || token.length > 5000) return null
  try {
    const parts = token.split(".")
    if (parts.length !== 2) return null
    const expected = Buffer.from(signature(parts[0], secret)); const supplied = Buffer.from(parts[1])
    if (expected.length !== supplied.length || !timingSafeEqual(expected, supplied)) return null
    const data = JSON.parse(Buffer.from(parts[0], "base64url").toString("utf8")) as ReviewToken
    if (!reviewIntent(data.action, data.record, data.target, data.reason) || data.actor !== actor || !validId(data.request) ||
      !/^[0-9a-f]{32}$/.test(data.fingerprint) || !Number.isSafeInteger(data.expires) || data.expires < now || data.expires > now + 15 * 60 * 1000) return null
    return data
  } catch { return null }
}

import "server-only"
import { createHmac, timingSafeEqual, randomUUID } from "node:crypto"

export const MAINTENANCE_FAMILIES = ["news", "originals", "news-source", "deals-source", "discovery-source"] as const
export type MaintenanceFamily = typeof MAINTENANCE_FAMILIES[number]
export type MaintenanceIntent = { action: "hide" | "pause" | "activate" | "restore" | "retry" | "reconcile"; family: MaintenanceFamily; record: string; reason: string; dryRun: boolean; runId?: string | null }
export type MaintenanceToken = MaintenanceIntent & { actor: string; fingerprint: string; request: string; expires: number }
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
export function maintenanceIntent(value: unknown): MaintenanceIntent | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null
  const v = value as MaintenanceIntent
  if (!MAINTENANCE_FAMILIES.includes(v.family) || !["hide", "pause", "activate", "restore", "retry", "reconcile"].includes(v.action) ||
    typeof v.record !== "string" || typeof v.reason !== "string" || v.reason.trim().length < 10 || v.reason.length > 1000 || typeof v.dryRun !== "boolean") return null
  if (v.action === "restore" || v.action === "reconcile") { if (!uuid.test(v.record)) return null }
  else if (v.family === "discovery-source") { if (!uuid.test(v.record)) return null }
  else if (v.family === "originals") { if (!/^(daily|weekly)-\d{4}-\d{2}-\d{2}$/.test(v.record)) return null }
  else if (!/^[1-9][0-9]{0,14}$/.test(v.record)) return null
  const source = v.family.endsWith("-source")
  if (v.action === "reconcile" ? (!/^[1-9][0-9]{0,14}$/.test(v.runId || "") || !["news", "originals"].includes(v.family)) : !!v.runId) return null
  if ((v.action === "hide" && source) || (["pause", "activate"].includes(v.action) && !source) || (v.action === "retry" && !["news", "originals"].includes(v.family))) return null
  return { action: v.action, family: v.family, record: v.record, reason: v.reason.trim(), dryRun: v.dryRun, runId: v.runId || null }
}
const mac = (payload: string, secret: string) => createHmac("sha256", secret).update("dadspace-maintenance-v1:" + payload).digest("base64url")
export function signMaintenance(intent: MaintenanceIntent, actor: string, fingerprint: string, secret: string, now = Date.now()) {
  if (!uuid.test(actor) || secret.length < 32 || !/^[a-f0-9]{32,64}$/.test(fingerprint)) throw new Error("Invalid signing context")
  const payload = Buffer.from(JSON.stringify({ ...intent, actor, fingerprint, request: randomUUID(), expires: now + 10 * 60_000 })).toString("base64url")
  return `${payload}.${mac(payload, secret)}`
}
export function verifyMaintenance(token: unknown, actor: string, secret: string, now = Date.now()): MaintenanceToken | null {
  if (typeof token !== "string" || token.length > 8000 || secret.length < 32) return null
  try {
    const [payload, signature, extra] = token.split(".")
    if (!payload || !signature || extra !== undefined) return null
    const expected = Buffer.from(mac(payload, secret)), actual = Buffer.from(signature)
    if (expected.length !== actual.length || !timingSafeEqual(expected, actual)) return null
    const v = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as MaintenanceToken
    if (!maintenanceIntent(v) || v.actor !== actor || !uuid.test(v.request) || !/^[a-f0-9]{32,64}$/.test(v.fingerprint) ||
      !Number.isSafeInteger(v.expires) || v.expires <= now || v.expires > now + 10 * 60_000) return null
    return v
  } catch { return null }
}

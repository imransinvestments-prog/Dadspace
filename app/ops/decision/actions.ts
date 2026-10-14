"use server"

import { revalidatePath } from "next/cache"
import { getSupabase } from "@/lib/supabase"
import { reviewIdentity } from "@/lib/operations/reviewer"
import { reviewIntent, signReview, verifyReview } from "@/lib/operations/review-token"

export type ReviewState = { message: string; preview?: { token: string; summary: string; venues: { id: string; name: string; postcode: string | null; public_visible: boolean }[]; listings: number; provenance: number }; audit?: string }
export async function previewDecision(_state: ReviewState, form: FormData): Promise<ReviewState> {
  const identity = await reviewIdentity()
  if (!identity) return { message: "Operator access could not be verified." }
  const intent = reviewIntent(form.get("action"), form.get("record"), form.get("target"), form.get("reason"))
  if (!intent || form.get("evidence") !== "reviewed") return { message: "Choose a valid decision and confirm source, identity and suitability evidence. A reason of 10–1,000 characters is required." }
  const secret = process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY
  if (!secret) return { message: "Review service is unavailable. No change made." }
  try {
    const db = getSupabase()
    if (!db) return { message: "Review service is unavailable. No change made." }
    const { data, error } = await db.rpc("dadspace_review_plan", { p_action: intent.action, p_record: intent.record, p_target: intent.target }).abortSignal(AbortSignal.timeout(10_000))
    if (error || !data || typeof data.summary !== "string" || !/^[0-9a-f]{32}$/.test(data.fingerprint) || !Array.isArray(data.venues) ||
      !Number.isSafeInteger(data.listings) || !Number.isSafeInteger(data.provenance)) return { message: "Preview unavailable: the record may have changed, lack required evidence or exceed the safe review limit. Refresh and review again." }
    return { message: identity.reviewer ? "Review this exact change before applying it." : "Preview only. Your account has read-only access; applying decisions requires a separately approved reviewer role.",
      preview: { token: signReview(intent, identity.id, data.fingerprint, secret), summary: data.summary,
        venues: data.venues.map((v: { id: string; name: string; postcode: string | null; public_visible: boolean }) => ({ id: v.id, name: v.name, postcode: v.postcode, public_visible: v.public_visible })),
        listings: data.listings, provenance: data.provenance } }
  } catch { return { message: "Review service is unavailable. No change made." } }
}
export async function applyDecision(_state: ReviewState, form: FormData): Promise<ReviewState> {
  const identity = await reviewIdentity()
  if (!identity?.reviewer) return { message: "Reviewer access is required. No change made." }
  const secret = process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY
  const intent = secret ? verifyReview(form.get("token"), identity.id, secret) : null
  if (!intent || form.get("confirm") !== "apply") return { message: "The preview expired or confirmation is missing. Generate a fresh preview." }
  try {
    const db = getSupabase()
    if (!db) return { message: "Review service is unavailable. No change made." }
    const { data, error } = await db.rpc("dadspace_review_apply", { p_actor: identity.id, p_request: intent.request, p_action: intent.action,
      p_record: intent.record, p_target: intent.target, p_expected: intent.fingerprint, p_reason: intent.reason }).abortSignal(AbortSignal.timeout(15_000))
    if (error || typeof data !== "string") return { message: "Decision not applied. Records may have changed, a duplicate identity may conflict, or the service may be unavailable. Refresh evidence and preview again." }
    revalidatePath("/ops", "layout"); revalidatePath("/venues", "layout"); revalidatePath("/activities", "layout"); revalidatePath("/events", "layout")
    return { message: "Decision recorded. Refresh the queue to see the current state. Rollback is available while the affected evidence remains unchanged.", audit: data }
  } catch { return { message: "The result could not be confirmed. Check decision history before retrying; the same signed request cannot apply twice." } }
}

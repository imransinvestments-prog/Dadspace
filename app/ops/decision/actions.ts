"use server"

import { revalidatePath } from "next/cache"
import { getSupabase } from "@/lib/supabase"
import { reviewIdentity } from "@/lib/operations/reviewer"
import { reviewIntent, signReview, verifyReview } from "@/lib/operations/review-token"
import { editForm } from "@/lib/operations/review-edit"

export type ReviewState = { message: string; preview?: { token: string; summary: string; reason: string; patch?: { source_url: string; changes: Record<string, string | number | null> }; venues: { id: string; name: string; postcode: string | null; public_visible: boolean }[]; listings: number; provenance: number }; audit?: string }
export async function previewDecision(_state: ReviewState, form: FormData): Promise<ReviewState> {
  const identity = await reviewIdentity()
  if (!identity) return { message: "Operator access could not be verified." }
  const intent = reviewIntent(form.get("action"), form.get("record"), form.get("target"), form.get("reason"), form.get("action") === "edit" ? editForm(form) : null)
  if (!intent || form.get("evidence") !== "reviewed") return { message: "Choose a valid decision and confirm source, identity and suitability evidence. A reason of 10–1,000 characters is required." }
  const secret = process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY
  if (!secret) return { message: "Review service is unavailable. No change made." }
  try {
    const db = getSupabase()
    if (!db) return { message: "Review service is unavailable. No change made." }
    if (intent.action === "rollback") {
      const audit = await db.from("operations_review_audit").select("action").eq("id", intent.record).abortSignal(AbortSignal.timeout(10_000)).maybeSingle()
      if (audit.error || !audit.data || audit.data.action === "link") return { message: "This decision is unavailable for venue rollback. Listing matching is reviewed separately." }
    }
    // The legacy read-only plan has the same whole-row fingerprint as v2.
    // Allow inspection during rolling deployment; writes always require v2.
    let { data, error } = await db.rpc("dadspace_review_plan_v2", { p_action: intent.action, p_record: intent.record, p_target: intent.target, p_patch: intent.patch || {} }).abortSignal(AbortSignal.timeout(10_000))
    if (error?.code === "PGRST202") ({ data, error } = await db.rpc("dadspace_review_plan", { p_action: intent.action === "edit" || intent.action === "reject" ? "hide" : intent.action, p_record: intent.record, p_target: intent.target }).abortSignal(AbortSignal.timeout(10_000)))
    if (error || !data || typeof data.summary !== "string" || !/^[0-9a-f]{32}$/.test(data.fingerprint) || !Array.isArray(data.venues) ||
      !Number.isSafeInteger(data.listings) || !Number.isSafeInteger(data.provenance)) return { message: "Preview unavailable: the record may have changed, lack required evidence or exceed the safe review limit. Refresh and review again." }
    return { message: identity.reviewer ? "Review this exact change before applying it." : "Preview only. Your account has read-only access; applying decisions requires a separately approved reviewer role.",
      preview: { token: signReview(intent, identity.id, data.fingerprint, secret), summary: intent.action === "edit" ? "Correct only the selected facts. Publication, country attribution and listing relationships stay unchanged." : intent.action === "reject" ? "Reject this venue from public discovery, retaining its identity, evidence and relationships." : data.summary, reason: intent.reason,
        ...(intent.patch ? { patch: intent.patch } : {}),
        venues: data.venues.map((v: { id: string; name: string; postcode: string | null; public_visible: boolean }) => ({ id: v.id, name: v.name, postcode: v.postcode, public_visible: v.public_visible })),
        listings: data.listings, provenance: data.provenance } }
  } catch { return { message: "Review service is unavailable. No change made." } }
}
export async function applyDecision(_state: ReviewState, form: FormData): Promise<ReviewState> {
  if (process.env.VERCEL_ENV === "preview") return { message: "This preview is read-only. Production data decisions cannot be applied from a development deployment." }
  const identity = await reviewIdentity()
  if (!identity?.reviewer) return { message: "Reviewer access is required. No change made." }
  const secret = process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY
  const intent = secret ? verifyReview(form.get("token"), identity.id, secret) : null
  if (!intent || form.get("confirm") !== "apply") return { message: "The preview expired or confirmation is missing. Generate a fresh preview." }
  try {
    const db = getSupabase()
    if (!db) return { message: "Review service is unavailable. No change made." }
    const { data, error } = await db.rpc("dadspace_review_apply_v2", { p_actor: identity.id, p_request: intent.request, p_action: intent.action,
      p_record: intent.record, p_target: intent.target, p_expected: intent.fingerprint, p_reason: intent.reason, p_patch: intent.patch || {} }).abortSignal(AbortSignal.timeout(15_000))
    if (error || typeof data !== "string") return { message: ["P0001", "23505", "23503", "55P03", "57014"].includes(error?.code || "") ?
      "Decision not applied. Records changed, an identity conflicted, or the transaction was blocked. Refresh evidence and preview again." :
      "The result could not be confirmed. Check decision history before retrying; the same signed request cannot apply twice." }
    revalidatePath("/", "layout")
    return { message: "Decision recorded. Refresh the queue to see the current state. Rollback is available while the affected evidence remains unchanged.", audit: data }
  } catch { return { message: "The result could not be confirmed. Check decision history before retrying; the same signed request cannot apply twice." } }
}

"use client"
import { useActionState } from "react"
import { saveReview } from "./actions"
import { REVIEW_DECISIONS } from "@/lib/operations/review-tasks"
import { useRouter } from "next/navigation"
import { ORIGINALS_CHECKS } from "@/lib/operations/originals-checks"
export default function ReviewForm({ id, version, disabledReason, record, previousChecks }: { id: number; version: string; disabledReason?: string; record?: { rowId: string; fingerprint: string; page: number }; previousChecks?: Record<string, string> }) {
  const [state, action, pending] = useActionState(saveReview, { message: "", ok: false })
  const router = useRouter()
  return <form action={action} className="space-y-4 rounded-2xl border p-6">
    <h2 className="text-xl font-bold">{record ? "Decision on this record" : "Overall review decision"}</h2>
    <p className="text-sm text-muted-foreground">{record ? "The displayed record and its fingerprint are saved with your decision. " : "State the exact scope of your acceptance. "}Notes are saved publicly to the GitHub task. Approval records your review; it does not change or publish the underlying data.</p>
    {disabledReason && <p role="status" className="rounded-lg border p-3 text-sm">Saving is unavailable until the setup issues at the top of this page are resolved. Evidence is optional and does not block saving.</p>}
    <input type="hidden" name="id" value={id}/><input type="hidden" name="version" value={version}/>
    {record && <><input type="hidden" name="rowId" value={record.rowId}/><input type="hidden" name="fingerprint" value={record.fingerprint}/><input type="hidden" name="page" value={record.page}/></>}
    <label className="block">Decision<select name="decision" defaultValue="" required className="mt-2 block w-full rounded border bg-background p-3"><option value="" disabled>Choose a decision</option>{REVIEW_DECISIONS.map(value => <option key={value}>{value}</option>)}</select></label>
    {id === 126 && record && <fieldset className="space-y-3"><legend className="font-semibold">Article checks</legend><p className="text-sm text-muted-foreground">Score only what you have checked. Earlier approvals are retained without assuming that attribution, location or links were verified.</p>{Object.entries({ relevance: "Useful for dads/families in its intended area?", attribution: "Correct publisher attribution?", destination: "Did the article link open the correct destination?", geography: "Does the stored geographic targeting match the article?" }).map(([key, label]) => <label key={key} className="block text-sm">{label}<select name={`check_${key}`} defaultValue={previousChecks?.[key] || "unknown"} className="mt-1 block w-full rounded border bg-background p-3"><option value="unknown">Not checked / unsure</option><option value="yes">Yes</option><option value="no">No — needs attention</option></select></label>)}</fieldset>}
    {id === 128 && record && <fieldset className="space-y-4"><legend className="font-semibold">Originals editorial checks</legend><p className="text-sm text-muted-foreground">Record each judgement explicitly for new or updated reviews. Existing approvals remain recorded; unchecked fields do not imply a pass.</p>{ORIGINALS_CHECKS.map(({ key, label, help }) => <label key={key} className="block text-sm"><span className="font-semibold">{label}</span><span className="mt-1 block text-muted-foreground">{help}</span><select name={`editorial_${key}`} aria-label={label} defaultValue={previousChecks?.[key] || "unknown"} className="mt-2 block w-full rounded border bg-background p-3"><option value="unknown">Not checked / unsure</option><option value="yes">Pass</option><option value="no">Needs changes</option></select></label>)}</fieldset>}
    <label className="block">Scope, reason and required follow-up<textarea name="notes" required maxLength={6000} rows={5} className="mt-2 block w-full rounded border bg-background p-3"/></label>
    <label className="block">Evidence links, sample IDs and scores (optional)<textarea name="evidence" aria-required={false} placeholder="Leave blank if you have no additional evidence." maxLength={2000} rows={3} className="mt-2 block w-full rounded border bg-background p-3"/></label>
    <button disabled={!!disabledReason || pending || state.ok} title={disabledReason ? "Resolve the setup issues at the top of the page to enable saving." : undefined} className="rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:opacity-50">{disabledReason ? "Saving unavailable — setup required" : pending ? "Saving…" : state.ok ? "Decision saved" : "Save decision to GitHub"}</button>
    {state.ok && <button type="button" onClick={() => router.refresh()} className="ml-3 underline">Refresh evidence and continue reviewing</button>}
    {state.message && <p role="status" aria-live="polite">{state.message}</p>}
  </form>
}

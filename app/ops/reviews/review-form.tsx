"use client"
import { useActionState } from "react"
import { saveReview } from "./actions"
import { REVIEW_DECISIONS } from "@/lib/operations/review-tasks"
import { useRouter } from "next/navigation"
export default function ReviewForm({ id, version, disabledReason, record }: { id: number; version: string; disabledReason?: string; record?: { rowId: string; fingerprint: string; page: number } }) {
  const [state, action, pending] = useActionState(saveReview, { message: "", ok: false })
  const router = useRouter()
  return <form action={action} className="space-y-4 rounded-2xl border p-6">
    <h2 className="text-xl font-bold">{record ? "Decision on this record" : "Overall review decision"}</h2>
    <p className="text-sm text-muted-foreground">{record ? "The displayed record and its fingerprint are saved with your decision. " : "State the exact scope of your acceptance. "}Notes are saved publicly to the GitHub task. Approval records your review; it does not change or publish the underlying data.</p>
    {disabledReason && <p role="status" className="rounded-lg border p-3 text-sm">{disabledReason}</p>}
    <input type="hidden" name="id" value={id}/><input type="hidden" name="version" value={version}/>
    {record && <><input type="hidden" name="rowId" value={record.rowId}/><input type="hidden" name="fingerprint" value={record.fingerprint}/><input type="hidden" name="page" value={record.page}/></>}
    <label className="block">Decision<select name="decision" defaultValue="" required className="mt-2 block w-full rounded border bg-background p-3"><option value="" disabled>Choose a decision</option>{REVIEW_DECISIONS.map(value => <option key={value}>{value}</option>)}</select></label>
    <label className="block">Scope, reason and required follow-up<textarea name="notes" required maxLength={6000} rows={5} className="mt-2 block w-full rounded border bg-background p-3"/></label>
    <label className="block">Evidence links, sample IDs and scores<textarea name="evidence" maxLength={2000} rows={3} className="mt-2 block w-full rounded border bg-background p-3"/></label>
    <button disabled={!!disabledReason || pending || state.ok} className="rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:opacity-50">{pending ? "Saving…" : state.ok ? "Decision saved" : "Save decision to GitHub"}</button>
    {state.ok && <button type="button" onClick={() => router.refresh()} className="ml-3 underline">Refresh evidence and continue reviewing</button>}
    {state.message && <p role="status" aria-live="polite">{state.message}</p>}
  </form>
}

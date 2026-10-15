"use client"
import { useActionState } from "react"
import { saveReview } from "./actions"
import { REVIEW_DECISIONS } from "@/lib/operations/review-tasks"
export default function ReviewForm({ id, version }: { id: number; version: string }) {
  const [state, action, pending] = useActionState(saveReview, { message: "", ok: false })
  return <form action={action} className="space-y-4 rounded-2xl border p-6">
    <h2 className="text-xl font-bold">Record your review</h2>
    <p className="text-sm text-muted-foreground">Review the evidence and criteria first. Notes are saved publicly to this GitHub task; include only information suitable for the repository.</p>
    <input type="hidden" name="id" value={id}/><input type="hidden" name="version" value={version}/>
    <label className="block">Decision<select name="decision" defaultValue="" required className="mt-2 block w-full rounded border bg-background p-3"><option value="" disabled>Choose a decision</option>{REVIEW_DECISIONS.map(value => <option key={value}>{value}</option>)}</select></label>
    <label className="block">Scope, reason and required follow-up<textarea name="notes" required maxLength={6000} rows={5} className="mt-2 block w-full rounded border bg-background p-3"/></label>
    <label className="block">Evidence links, sample IDs and scores<textarea name="evidence" maxLength={2000} rows={3} className="mt-2 block w-full rounded border bg-background p-3"/></label>
    <button disabled={pending || state.ok} className="rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:opacity-50">{pending ? "Saving…" : state.ok ? "Decision saved" : "Save decision to GitHub"}</button>
    {state.message && <p role="status" aria-live="polite">{state.message}</p>}
  </form>
}

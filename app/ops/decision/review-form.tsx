"use client"
import { useActionState } from "react"
import { previewDecision, applyDecision, type ReviewState } from "./actions"

export default function ReviewForm({ record, listing, rollback, reviewer, targets }: { record: string; listing: boolean; rollback: boolean; reviewer: boolean; targets: { id: string; venue_name: string; postcode: string | null }[] }) {
  const [preview, previewAction, previewPending] = useActionState<ReviewState, FormData>(previewDecision, { message: "" })
  const [applied, applyAction, applyPending] = useActionState<ReviewState, FormData>(applyDecision, { message: "" })
  return <div className="space-y-6">
    <form action={previewAction} className="rounded-2xl border bg-card p-6 space-y-4">
      <input type="hidden" name="record" value={record}/>
      <label className="block font-semibold">Decision<select name="action" className="mt-2 block w-full rounded-lg border bg-background p-3" defaultValue={rollback ? "rollback" : listing ? "link" : "approve"}>{rollback ? <option value="rollback">Roll back this decision</option> : listing ? <option value="link">Link to a canonical venue</option> : <><option value="approve">Approve and publish venue</option><option value="hide">Hide / reject venue</option><option value="merge">Merge duplicate into canonical venue</option></>}</select></label>
      {!rollback && <label className="block font-semibold">Canonical venue (merge / link only)<select name="target" className="mt-2 block w-full rounded-lg border bg-background p-3"><option value="">No target (approve / hide)</option>{targets.map(target => <option key={target.id} value={target.id}>{target.venue_name} · {target.postcode || "Postcode missing"}</option>)}</select></label>}
      <label className="block font-semibold">Decision reason<textarea name="reason" required minLength={10} maxLength={1000} rows={3} className="mt-2 block w-full rounded-lg border bg-background p-3"/></label>
      <label className="flex items-start gap-3 text-sm"><input type="checkbox" name="evidence" value="reviewed" required className="mt-1"/><span>I reviewed source access/rights, place identity, branch/location and suitability. A shared name or postcode alone is not a match. For rollback I reviewed the previous decision.</span></label>
      <button disabled={previewPending || applyPending} className="rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground">{previewPending ? "Loading preview…" : "Preview decision"}</button>
    </form>
    {preview.message && <p role="status" className="rounded-xl border p-4">{preview.message}</p>}
    {preview.preview && !applied.audit && <section className="rounded-2xl border bg-card p-6 space-y-4"><h2 className="text-xl font-bold">Change preview</h2><p>{preview.preview.summary}</p><p><strong>Recorded reason:</strong> {preview.preview.reason}</p><p className="text-sm text-muted-foreground">Form edits require a new preview; this confirmation applies the signed preview below.</p><ul className="space-y-2">{preview.preview.venues.map(venue => <li key={venue.id}>{venue.name} · {venue.postcode || "Postcode missing"} · Currently {venue.public_visible ? "public" : "hidden"}</li>)}</ul><p className="text-sm">Snapshot includes {preview.preview.listings} listing relationships and {preview.preview.provenance} provenance records. Every imported change invalidates this preview. It expires in 15 minutes.</p>
      <form action={applyAction} className="space-y-4"><input type="hidden" name="token" value={preview.preview.token}/><label className="flex items-start gap-3 text-sm"><input type="checkbox" name="confirm" value="apply" required disabled={!reviewer} className="mt-1"/><span>Apply this exact reviewed change and record my identity, reason and before/after evidence.</span></label><button disabled={!reviewer || applyPending || previewPending} className="rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground">{applyPending ? "Applying…" : reviewer ? "Apply reviewed decision" : "Reviewer role required"}</button></form>
    </section>}
    {applied.message && <p role="status" className="rounded-xl border p-4">{applied.message}{applied.audit && <span className="mt-2 block break-all text-xs">Decision ID: {applied.audit}</span>}</p>}
  </div>
}

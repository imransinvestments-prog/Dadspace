"use client"
import { useActionState, useState, type ChangeEvent } from "react"
import { preview, apply } from "./actions"

function ApplyForm({ token }: { token: string }) {
  const [result, applyAction, applying] = useActionState(apply, { message: "" })
  return <div><form action={applyAction} className="mt-5 space-y-4"><input type="hidden" name="token" value={token} /><label className="flex gap-3"><input type="checkbox" name="confirm" value="apply" required />I approve this exact action and its stated scope.</label><button disabled={applying || result.ok} className="rounded-lg border px-5 py-3 font-semibold disabled:opacity-50">{applying ? "Submitting once…" : result.ok ? "Request recorded" : "Apply approved action"}</button></form><p role="status" className="mt-4">{result.message}</p></div>
}
export default function MaintenanceForm({ initial }: { initial: { family: string; action: string; record: string } }) {
  const [plan, planAction, planning] = useActionState(preview, { message: "" })
  const [values, setValues] = useState({ ...initial, reason: "", runId: "", dryRun: true })
  function change(event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    const target = event.currentTarget
    const value = target instanceof HTMLInputElement && target.type === "checkbox" ? target.checked : target.value
    setValues(previous => ({ ...previous, [target.name]: value }))
  }
  return <section className="rounded-2xl border bg-card p-6"><h2 className="text-xl font-bold">Preview a maintenance action</h2>
    <p className="mt-2 text-sm text-muted-foreground">Use the exact record ID from the queue. Restore uses the original audit request ID. A source activation needs reviewed source-policy evidence in the reason.</p>
    <form action={planAction} className="mt-5 grid gap-4 sm:grid-cols-2">
      <label className="grid min-w-0 gap-2">Area<select name="family" value={values.family} onChange={change} className="min-w-0 w-full rounded-lg border bg-background p-3"><option value="news">News article</option><option value="originals">Originals slot</option><option value="news-source">News source</option><option value="deals-source">Deals source</option><option value="discovery-source">Discovery source</option></select></label>
      <label className="grid min-w-0 gap-2">Action<select name="action" value={values.action} onChange={change} className="min-w-0 w-full rounded-lg border bg-background p-3"><option value="hide">Unpublish / hide</option><option value="retry">Bounded retry (News or Originals)</option><option value="restore">Restore previous audited state</option><option value="reconcile">Reconcile uncertain dispatch with completed run</option><option value="pause">Pause source</option><option value="activate">Activate reviewed source</option></select></label>
      <label className="grid min-w-0 gap-2">Record / slot / audit ID<input name="record" value={values.record} onChange={change} required maxLength={100} className="min-w-0 w-full rounded-lg border bg-background p-3" /></label>
      <label className="flex items-center gap-3"><input name="dryRun" type="checkbox" checked={values.dryRun} onChange={change} />Retry without publishing (may still incur model cost)</label>
      <label className="grid min-w-0 gap-2 sm:col-span-2">Completed workflow run ID (reconcile only; otherwise leave blank)<input name="runId" value={values.runId} onChange={change} inputMode="numeric" maxLength={15} className="min-w-0 w-full rounded-lg border bg-background p-3" /></label>
      <label className="grid min-w-0 gap-2 sm:col-span-2">Reason and evidence<textarea name="reason" value={values.reason} onChange={change} placeholder="Explain why you are considering this action (at least 10 characters)." minLength={10} maxLength={1000} required className="min-w-0 w-full rounded-lg border bg-background p-3" /></label>
      <button disabled={planning} className="rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground disabled:opacity-50">{planning ? "Checking current evidence…" : "Prepare preview"}</button>
    </form>
    <div aria-live="polite" className="mt-4 space-y-3"><p>{plan.message}</p>{plan.description && <p className="font-semibold">{plan.description}</p>}{plan.cost && <p className="text-sm">{plan.cost}</p>}</div>
    {plan.token && plan.canApply && <ApplyForm key={plan.token} token={plan.token} />}
  </section>
}

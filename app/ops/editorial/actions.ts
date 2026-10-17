"use server"
import { revalidatePath } from "next/cache"
import { previewMaintenance, applyMaintenance } from "@/lib/operations/maintenance"
export type MaintenanceState = { message: string; token?: string | null; canApply?: boolean; description?: string; cost?: string; ok?: boolean }
export async function preview(_: MaintenanceState, form: FormData): Promise<MaintenanceState> {
  try {
    const result = await previewMaintenance({ action: form.get("action"), family: form.get("family"), record: form.get("record"), reason: form.get("reason"), dryRun: form.get("dryRun") === "on", runId: String(form.get("runId") || "") || null })
    return { ...result, message: result.canApply ? "Check this exact preview before confirming." : "Preview only. Live actions require separately configured maintenance permission and an approved production release." }
  } catch { return { message: "Preview unavailable. Check the record, schema/configuration and current evidence, then reload. No live action was submitted." } }
}
export async function apply(_: MaintenanceState, form: FormData): Promise<MaintenanceState> {
  if (form.get("confirm") !== "apply") return { message: "Confirm the exact preview first." }
  try {
    const id = await applyMaintenance(form.get("token"))
    revalidatePath("/ops/editorial"); revalidatePath("/news"); revalidatePath("/originals"); revalidatePath("/")
    return { ok: true, message: `Request recorded: ${id}. Check the audit and runner for the actual outcome before another request.` }
  } catch { return { message: "Outcome could not be confirmed. Inspect the audit and runner before retrying. A failed response does not prove that nothing happened." } }
}

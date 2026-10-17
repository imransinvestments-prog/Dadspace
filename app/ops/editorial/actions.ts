"use server"
import { revalidatePath } from "next/cache"
import { previewMaintenance, applyMaintenance } from "@/lib/operations/maintenance"
import { maintenanceIntent } from "@/lib/operations/maintenance-token"
export type MaintenanceState = { message: string; token?: string | null; canApply?: boolean; description?: string; cost?: string; ok?: boolean }
export async function preview(_: MaintenanceState, form: FormData): Promise<MaintenanceState> {
  const reason = String(form.get("reason") || "").trim()
  if (reason.length < 10 || reason.length > 1000) return { message: "Enter a detailed reason of 10–1,000 characters before preparing the preview. No action was submitted." }
  const intent = maintenanceIntent({ action: form.get("action"), family: form.get("family"), record: form.get("record"), reason, dryRun: form.get("dryRun") === "on", runId: String(form.get("runId") || "") || null })
  if (!intent) return { message: "Check that the area, action and record ID match. A completed run ID is needed only for reconciliation. No action was submitted." }
  try {
    const result = await previewMaintenance(intent)
    return { ...result, message: result.canApply ? "Check this exact preview before confirming." : "Preview only. Live actions require separately configured maintenance permission and an approved production release." }
  } catch { return { message: "Preview unavailable. Check the record, schema/configuration and current evidence, then reload. No live action was submitted." } }
}
export async function apply(_: MaintenanceState, form: FormData): Promise<MaintenanceState> {
  if (form.get("confirm") !== "apply") return { message: "Confirm the exact preview first." }
  try {
    const id = await applyMaintenance(form.get("token"))
    revalidatePath("/ops/editorial"); revalidatePath("/ops/deals"); revalidatePath("/ops"); revalidatePath("/news"); revalidatePath("/originals"); revalidatePath("/")
    return { ok: true, message: `Request recorded: ${id}. Check the audit and runner for the actual outcome before another request.` }
  } catch { return { message: "Outcome could not be confirmed. Inspect the audit and runner before retrying. A failed response does not prove that nothing happened." } }
}

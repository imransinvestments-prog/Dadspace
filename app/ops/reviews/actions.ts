"use server"
import { revalidatePath } from "next/cache"
import { recordTaskReview } from "@/lib/operations/task-review"
export async function saveReview(_: { message: string; ok: boolean }, form: FormData) {
  try {
    const id = Number(form.get("id"))
    const rowId = String(form.get("rowId") || "")
    await recordTaskReview(id, String(form.get("decision") || ""), String(form.get("notes") || ""), String(form.get("evidence") || ""), String(form.get("version") || ""), rowId ? { rowId, fingerprint: String(form.get("fingerprint") || ""), page: Number(form.get("page")) } : undefined)
    revalidatePath(`/ops/reviews/${id}`)
    revalidatePath("/ops/reviews")
    return { ok: true, message: "Decision saved to the GitHub task. Outstanding delivery gates remain open." }
  } catch {
    return { ok: false, message: "Could not confirm saving. Check the task history before retrying, then reload. Reviewer permission, GitHub configuration or changed evidence may need attention." }
  }
}

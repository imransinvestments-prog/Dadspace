"use server"
import { revalidatePath } from "next/cache"
import { recordTaskReview } from "@/lib/operations/task-review"
import { ORIGINALS_CHECKS, type OriginalsChecks } from "@/lib/operations/originals-checks"
import { NEWS_CHECK_LABELS, type NewsChecks } from "@/lib/operations/news-checks"
export async function saveReview(_: { message: string; ok: boolean }, form: FormData) {
  try {
    const id = Number(form.get("id"))
    const rowId = String(form.get("rowId") || "")
    const checks = id === 126 ? Object.fromEntries(Object.keys(NEWS_CHECK_LABELS).map(key => [key, String(form.get(`check_${key}`) || "unknown")])) as NewsChecks : undefined
    const editorialChecks = id === 128 ? Object.fromEntries(ORIGINALS_CHECKS.map(({ key }) => [key, String(form.get(`editorial_${key}`) || "unknown")])) as OriginalsChecks : undefined
    await recordTaskReview(id, String(form.get("decision") || ""), String(form.get("notes") || ""), String(form.get("evidence") || ""), String(form.get("version") || ""), rowId ? { rowId, fingerprint: String(form.get("fingerprint") || ""), page: Number(form.get("page")), checks, editorialChecks } : undefined)
    revalidatePath(`/ops/reviews/${id}`)
    revalidatePath("/ops/reviews")
    return { ok: true, message: "Decision saved to the GitHub task. Outstanding delivery gates remain open." }
  } catch {
    return { ok: false, message: "Could not confirm saving. Check the task history before retrying, then reload. Reviewer permission, GitHub configuration or changed evidence may need attention." }
  }
}

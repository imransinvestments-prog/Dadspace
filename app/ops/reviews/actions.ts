"use server"
import { revalidatePath } from "next/cache"
import { recordTaskReview } from "@/lib/operations/task-review"
export async function saveReview(_: { message: string; ok: boolean }, form: FormData) {
  try {
    await recordTaskReview(Number(form.get("id")), String(form.get("decision") || ""), String(form.get("notes") || ""), String(form.get("evidence") || ""), String(form.get("version") || ""))
    revalidatePath("/ops/reviews")
    return { ok: true, message: "Decision saved to the GitHub task. Outstanding delivery gates remain open." }
  } catch {
    return { ok: false, message: "Could not confirm saving. Check the task history before retrying, then reload. Reviewer permission, GitHub configuration or changed evidence may need attention." }
  }
}

import "server-only"
import { createClient } from "@/lib/supabase/server"
import { isOperationsUser, isVerifiedOperationsEmail } from "./access"

export async function reviewIdentity() {
  try {
    const { data, error } = await (await createClient()).auth.getUser()
    const user = data.user
    if (error || !user || user.is_anonymous) return null
    if (!(isOperationsUser(user.id, process.env.DADSPACE_OPERATOR_USER_IDS) ||
      isVerifiedOperationsEmail(user, process.env.DADSPACE_OPERATOR_EMAILS))) return null
    return { id: user.id, reviewer: isOperationsUser(user.id, process.env.DADSPACE_REVIEWER_USER_IDS) }
  } catch { return null }
}

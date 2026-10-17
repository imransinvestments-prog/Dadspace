import "server-only"
import { createClient } from "@/lib/supabase/server"
import { isOperationsOwner } from "./access"

// Every entry point verifies the server identity before any privileged reads.
export async function operationsAccess(): Promise<"allowed" | "denied" | "sign-in" | "unavailable"> {
  if (!process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL || !process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY) return "unavailable"
  try {
    const { data, error } = await (await createClient()).auth.getUser()
    if (error || !data.user) return "sign-in"
    if (data.user.is_anonymous) return "denied"
    return isOperationsOwner(data.user) ? "allowed" : "denied"
  } catch { return "unavailable" }
}

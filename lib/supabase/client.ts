import { createBrowserClient } from "@supabase/ssr"
import type { SupabaseClient } from "@supabase/supabase-js"

let browserClient: SupabaseClient | undefined

export function createClient() {
  if (typeof window !== 'undefined' && browserClient) return browserClient
  const client = createBrowserClient(
    process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY!,
    { isSingleton: typeof window !== 'undefined', cookieOptions: { secure: process.env.NODE_ENV === "production" } },
  )
  if (typeof window !== 'undefined') browserClient = client
  return client
}

import "server-only"
import { createClient, type SupabaseClient } from "@supabase/supabase-js"

let client: SupabaseClient | null = null

/**
 * Server-only, read-only client. The tables are protected by RLS, so anon reads
 * return zero rows; a server-side service key lets the app read them without
 * changing any database policies. The app only ever calls `select`.
 */
export function getSupabase(): SupabaseClient | null {
  const url = process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL
  const key =
    process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY ?? process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY
  if (!url || !key) return null
  if (!client) {
    client = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } })
  }
  return client
}

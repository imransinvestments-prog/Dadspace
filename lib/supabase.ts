import "server-only"
import { createClient, type SupabaseClient } from "@supabase/supabase-js"

let client: SupabaseClient | null = null

const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * The gateway occasionally rejects a valid secret key's per-request token with
 * 401 PGRST303 (about 0.8% of requests in October 2026). That rejection happens
 * during token validation, before any query runs, so one retry cannot repeat
 * work. Bodies that cannot be re-sent are passed through unchanged.
 */
export function withTokenRetry(fetchImpl: typeof fetch, pause: (ms: number) => Promise<unknown> = wait): typeof fetch {
  return async (input, init) => {
    const response = await fetchImpl(input, init)
    const resendable = init?.body == null || typeof init.body === "string"
    if (response.status !== 401 || !resendable || init?.signal?.aborted) return response
    const rejected = response.headers.get("proxy-status")?.includes("PGRST303")
      || await response.clone().json().then(body => body?.code === "PGRST303", () => false)
    if (!rejected) return response
    await pause(200)
    return fetchImpl(input, init)
  }
}

/**
 * Server-only, read-only client. The tables are protected by RLS, so anon reads
 * return zero rows; a server-side service key lets the app read them without
 * changing any database policies. The app only ever calls `select`, except the
 * /api/vitals beacon, which inserts validated rows into `web_vitals` only.
 */
export function getSupabase(): SupabaseClient | null {
  const url = process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL
  // An anonymous RLS-empty result must never masquerade as genuine empty supply.
  const key = process.env.DADSPACE_SUPABASE_SERVICE_ROLE_KEY
  if (!url || !key) return null
  if (!client) {
    client = createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false }, global: { fetch: withTokenRetry((input, init) => fetch(input, init)) } })
  }
  return client
}

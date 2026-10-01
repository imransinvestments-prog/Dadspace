import { createServerClient } from "@supabase/ssr"
import { cookies } from "next/headers"

/**
 * Create a new client per request — never cache it in a module-level variable,
 * because it carries the signed-in user's cookies.
 */
export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY!,
    {
      cookieOptions: { secure: process.env.NODE_ENV === "production" },
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) => cookieStore.set(name, value, options))
          } catch {
            // Called from a Server Component, where cookies are read-only.
            // Safe to ignore because proxy.ts refreshes the session.
          }
        },
      },
    },
  )
}

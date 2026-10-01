import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"
import { isProtectedPath } from "@/lib/auth/redirect"

export async function updateSession(request: NextRequest) {
  const url = process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL
  const anonKey = process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY
  if (!url || !anonKey) return NextResponse.next({ request })

  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(url, anonKey, {
    cookieOptions: { secure: process.env.NODE_ENV === "production" },
    cookies: {
      getAll() {
        return request.cookies.getAll()
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
        supabaseResponse = NextResponse.next({ request })
        cookiesToSet.forEach(({ name, value, options }) => supabaseResponse.cookies.set(name, value, options))
      },
    },
  })

  // Must run straight after creating the client: it refreshes expired sessions.
  const {
    data: { user },
  } = await supabase.auth.getUser()

  const { pathname, search } = request.nextUrl
  if (!user && isProtectedPath(pathname)) {
    const loginUrl = request.nextUrl.clone()
    loginUrl.pathname = "/auth/login"
    loginUrl.search = ""
    loginUrl.searchParams.set("next", `${pathname}${search}`)
    const redirect = NextResponse.redirect(loginUrl)
    supabaseResponse.cookies.getAll().forEach((cookie) => redirect.cookies.set(cookie))
    return redirect
  }

  return supabaseResponse
}

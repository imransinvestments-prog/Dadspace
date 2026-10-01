import { NextResponse, type NextRequest } from "next/server"
import { createClient } from "@/lib/supabase/server"
import { NEXT_COOKIE, safeNext } from "@/lib/auth/redirect"

export async function GET(request: NextRequest) {
  const { searchParams, origin } = request.nextUrl
  const code = searchParams.get("code")
  const cookieNext = request.cookies.get(NEXT_COOKIE)?.value
  const next = safeNext(searchParams.get("next") ?? (cookieNext ? decodeURIComponent(cookieNext) : null))

  let destination = `${origin}/auth/error`
  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) destination = `${origin}${next}`
    else console.error("Auth callback error:", error.code ?? error.message)
  }

  const response = NextResponse.redirect(destination)
  response.cookies.delete(NEXT_COOKIE)
  return response
}

import { NextResponse, type NextRequest } from "next/server"
import { COMING_SOON } from "@/lib/launch"
import { updateSession } from "@/lib/supabase/proxy"

export async function proxy(request: NextRequest) {
  if (COMING_SOON) {
    const url = request.nextUrl.clone()
    url.pathname = "/"
    url.search = ""
    const response = NextResponse.rewrite(url)
    response.headers.set("Cache-Control", "no-store")
    if (request.nextUrl.pathname !== "/") response.headers.set("X-Robots-Tag", "noindex, follow")
    return response
  }
  return updateSession(request)
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|api/|favicon.ico|manifest.webmanifest|sw.js|robots.txt|sitemap.xml|images/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|js|css|txt|xml)$).*)",
  ],
}

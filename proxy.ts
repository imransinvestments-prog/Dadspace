import type { NextRequest } from "next/server"
import { updateSession } from "@/lib/supabase/proxy"

export async function proxy(request: NextRequest) {
  return updateSession(request)
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|api/|favicon.ico|manifest.webmanifest|sw.js|robots.txt|sitemap.xml|images/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|js|css|txt|xml)$).*)",
  ],
}

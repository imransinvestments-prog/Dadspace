export const PROTECTED_PREFIXES = ["/profile", "/chat"]
export const NEXT_COOKIE = "dadspace_auth_next"

export function isProtectedPath(pathname: string) {
  return PROTECTED_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))
}

/** Only allow same-site relative paths, so `?next=` can't send people to another website. */
export function safeNext(value: string | null | undefined, fallback = "/") {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.startsWith("/\\")) return fallback
  return value
}

/**
 * Where Supabase should send people back to after an email link or Google sign-in.
 * The destination is also stored in a short-lived cookie, in case a redirect drops the query string.
 */
export function authCallbackUrl(next: string) {
  const destination = safeNext(next)
  document.cookie = `${NEXT_COOKIE}=${encodeURIComponent(destination)}; path=/; max-age=900; samesite=lax`

  const base = process.env.NEXT_PUBLIC_DEV_SUPABASE_REDIRECT_URL ?? `${window.location.origin}/auth/callback`
  const url = new URL(base)
  url.searchParams.set("next", destination)
  return url.toString()
}

"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useState } from "react"
import { LogOut } from "lucide-react"
import { createClient } from "@/lib/supabase/client"
import { isProtectedPath } from "@/lib/auth/redirect"
import { useAuthUser, type AuthUserSummary } from "./use-auth-user"
import { cn } from "@/lib/utils"

export function Avatar({ user, className }: { user: Pick<AuthUserSummary, "displayName" | "avatarUrl">; className?: string }) {
  if (user.avatarUrl) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- avatars come from Supabase Storage or Google, any host
      <img src={user.avatarUrl} alt="" referrerPolicy="no-referrer" className={cn("rounded-full object-cover", className)} />
    )
  }
  return (
    <span aria-hidden className={cn("flex items-center justify-center rounded-full bg-highlight font-heading font-extrabold text-highlight-foreground", className)}>
      {user.displayName.charAt(0).toUpperCase()}
    </span>
  )
}

function useLogOut() {
  const router = useRouter()
  const pathname = usePathname()
  const [pending, setPending] = useState(false)

  async function logOut() {
    setPending(true)
    await createClient().auth.signOut()
    if (isProtectedPath(pathname)) router.replace("/")
    router.refresh()
    setPending(false)
  }
  return { logOut, pending }
}

function loginHref(pathname: string) {
  return pathname.startsWith("/auth") || pathname === "/" ? "/auth/login" : `/auth/login?next=${encodeURIComponent(pathname)}`
}

export function SidebarUserMenu() {
  const user = useAuthUser()
  const pathname = usePathname()
  const { logOut, pending } = useLogOut()

  if (user === undefined) return <div className="h-12 animate-pulse rounded-full bg-muted" aria-hidden />

  if (!user) {
    return (
      <div className="flex gap-2">
        <Link href={loginHref(pathname)} className="inline-flex h-11 flex-1 items-center justify-center rounded-full border font-semibold transition hover:bg-muted">
          Log in
        </Link>
        <Link href="/auth/sign-up" className="inline-flex h-11 flex-1 items-center justify-center rounded-full bg-primary font-semibold text-primary-foreground transition hover:opacity-90">
          Sign up
        </Link>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3 rounded-full border bg-background p-1.5 pr-2">
      <Link href="/profile" className="flex min-w-0 flex-1 items-center gap-3 rounded-full transition hover:opacity-80">
        <Avatar user={user} className="size-9 shrink-0 text-sm" />
        <span className="flex min-w-0 flex-col">
          <span className="truncate text-sm font-semibold">{user.displayName}</span>
          <span className="text-xs text-muted-foreground">View profile</span>
        </span>
      </Link>
      <button
        type="button"
        onClick={logOut}
        disabled={pending}
        aria-label="Log out"
        title="Log out"
        className="inline-flex size-9 shrink-0 items-center justify-center rounded-full text-muted-foreground transition hover:bg-muted hover:text-foreground disabled:opacity-60"
      >
        <LogOut className="size-4" aria-hidden />
      </button>
    </div>
  )
}

export function HeaderUserButton() {
  const user = useAuthUser()
  const pathname = usePathname()

  if (user === undefined) return <span className="size-11 animate-pulse rounded-full bg-muted" aria-hidden />

  if (!user) {
    return (
      <Link href={loginHref(pathname)} className="inline-flex h-11 items-center rounded-full bg-primary px-5 text-sm font-semibold text-primary-foreground">
        Log in
      </Link>
    )
  }

  return (
    <Link
      href="/profile"
      aria-label={`Your profile (${user.displayName})`}
      aria-current={pathname.startsWith("/profile") ? "page" : undefined}
      className="inline-flex size-11 items-center justify-center rounded-full"
    >
      <Avatar user={user} className="size-11 text-base" />
    </Link>
  )
}

export function LogOutButton() {
  const { logOut, pending } = useLogOut()
  return (
    <button
      type="button"
      onClick={logOut}
      disabled={pending}
      className="inline-flex h-12 items-center justify-center gap-2 rounded-full border px-6 font-semibold transition hover:bg-muted disabled:opacity-60"
    >
      <LogOut className="size-4" aria-hidden />
      {pending ? "Logging out…" : "Log out"}
    </button>
  )
}

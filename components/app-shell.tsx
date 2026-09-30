"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserRound } from "lucide-react"
import { Logo } from "./logo"
import { ThemeToggle } from "./theme-toggle"
import { InstallPrompt } from "./install-prompt"
import { NAV_ITEMS, isActive } from "./nav-items"
import { cn } from "@/lib/utils"

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="min-h-dvh">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:rounded-full focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground">
        Skip to content
      </a>

      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col gap-8 border-r bg-card px-5 py-6 lg:flex">
        <Logo />
        <nav aria-label="Main">
          <ul className="flex flex-col gap-1">
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
              const active = isActive(pathname, href)
              return (
                <li key={href}>
                  <Link
                    href={href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "flex h-12 items-center gap-3 rounded-full px-4 font-semibold transition",
                      active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <Icon className="size-5" aria-hidden />
                    {label}
                  </Link>
                </li>
              )
            })}
          </ul>
        </nav>
        <div className="mt-auto flex flex-col gap-4">
          <InstallPrompt variant="card" />
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">Made for UK dads</p>
            <ThemeToggle />
          </div>
        </div>
      </aside>

      <header className="sticky top-0 z-30 flex items-center justify-between border-b bg-background/85 px-4 py-3 backdrop-blur-md lg:hidden">
        <Logo />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link
            href="/profile"
            aria-label="Your profile"
            aria-current={isActive(pathname, "/profile") ? "page" : undefined}
            className="inline-flex size-11 items-center justify-center rounded-full bg-highlight text-highlight-foreground"
          >
            <UserRound className="size-5" aria-hidden />
          </Link>
        </div>
      </header>

      <main id="main" className="pb-28 lg:pb-12 lg:pl-64">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 pt-4 lg:px-10 lg:pt-10">
          <div className="lg:hidden">
            <InstallPrompt variant="banner" />
          </div>
          {children}
        </div>
      </main>

      <nav aria-label="Main" className="pb-safe fixed inset-x-0 bottom-0 z-30 border-t bg-card/95 backdrop-blur-md lg:hidden">
        <ul className="mx-auto flex max-w-lg items-stretch justify-around px-2">
          {NAV_ITEMS.filter((i) => i.mobile).map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href)
            return (
              <li key={href} className="flex-1">
                <Link
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex h-16 flex-col items-center justify-center gap-1 text-xs font-semibold transition",
                    active ? "text-primary" : "text-muted-foreground",
                  )}
                >
                  <span className={cn("flex h-8 w-14 items-center justify-center rounded-full transition", active && "bg-primary/15")}>
                    <Icon className="size-5" aria-hidden />
                  </span>
                  {label}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
    </div>
  )
}

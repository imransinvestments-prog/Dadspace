"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Logo } from "./logo"
import { HeaderUserButton, SidebarUserMenu } from "./auth/user-menu"
import { ThemeToggle } from "./theme-toggle"
import { InstallPrompt } from "./install-prompt"
import { NAV_ITEMS, isActive } from "./nav-items"
import { cn } from "@/lib/utils"
import { useEffect, useRef, useState } from "react"
import { MoreHorizontal } from "lucide-react"

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [moreOpen, setMoreOpen] = useState(false)
  const moreButton = useRef<HTMLButtonElement>(null)
  const morePanel = useRef<HTMLDivElement>(null)
  useEffect(() => setMoreOpen(false), [pathname])
  useEffect(() => { if (moreOpen) morePanel.current?.querySelector('a')?.focus() }, [moreOpen])

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
          <SidebarUserMenu />
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">Made for UK dads</p>
            <ThemeToggle />
          </div>
        </div>
      </aside>

      <header className="sticky top-0 z-30 flex h-header items-center justify-between gap-2 border-b bg-background/85 px-3 backdrop-blur-md lg:hidden">
        <Logo />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <HeaderUserButton />
        </div>
      </header>

      <main id="main" className="pb-28 lg:pb-12 lg:pl-64">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 pt-4 lg:px-10 lg:pt-10">
          {children}
          <div className="lg:hidden">
            <InstallPrompt variant="banner" />
          </div>
        </div>
      </main>

      <nav aria-label="Main" onKeyDown={event => { if (event.key === 'Escape' && moreOpen) { setMoreOpen(false); moreButton.current?.focus() } }} className="pb-safe fixed inset-x-0 bottom-0 z-30 border-t bg-card/95 backdrop-blur-md lg:hidden">
        {moreOpen && <div ref={morePanel} id="mobile-more-navigation" className="absolute inset-x-2 bottom-full mb-2 max-h-[65dvh] overflow-y-auto rounded-2xl border bg-card p-2 shadow-xl">
          <p className="px-3 py-2 text-sm font-semibold">More from Dadspace</p>
          {NAV_ITEMS.filter(item => !item.mobile).map(({href,label,icon:Icon}) => <Link key={href} href={href} onClick={() => setMoreOpen(false)} aria-current={isActive(pathname,href) ? 'page' : undefined} className={cn('flex min-h-12 items-center gap-3 rounded-xl px-3 font-semibold',isActive(pathname,href) ? 'bg-primary text-primary-foreground' : 'hover:bg-muted')}><Icon className="size-5" aria-hidden />{label}</Link>)}
        </div>}
        <ul className="mx-auto flex max-w-lg items-stretch justify-around px-2">
          {NAV_ITEMS.filter((i) => i.mobile).map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href)
            return (
              <li key={href} className="min-w-0 flex-1">
                <Link
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex h-16 flex-col items-center justify-center gap-1 text-xs font-semibold transition",
                    active ? "text-primary-ink" : "text-muted-foreground",
                  )}
                >
                  <span className={cn("flex h-8 w-full max-w-14 items-center justify-center rounded-full transition", active && "bg-primary/15")}>
                    <Icon className="size-5" aria-hidden />
                  </span>
                  {label}
                </Link>
              </li>
            )
          })}
          <li className="min-w-0 flex-1"><button ref={moreButton} type="button" aria-expanded={moreOpen} aria-controls="mobile-more-navigation" onClick={() => setMoreOpen(value => !value)} className={cn('flex h-16 w-full flex-col items-center justify-center gap-1 text-xs font-semibold',NAV_ITEMS.some(item => !item.mobile && isActive(pathname,item.href)) ? 'text-primary-ink' : 'text-muted-foreground')}><span className="flex h-8 items-center"><MoreHorizontal className="size-5" aria-hidden /></span>More</button></li>
        </ul>
      </nav>
    </div>
  )
}

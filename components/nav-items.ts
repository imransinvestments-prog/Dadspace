import { BookOpen, CalendarHeart, Dumbbell, Home, MapPinned, MessagesSquare, Newspaper, Settings, Tag, UserRound, type LucideIcon } from "lucide-react"
import { FORUM_ENABLED } from "@/lib/launch"

export type NavItem = { href: string; label: string; icon: LucideIcon; mobile: boolean }

export const NAV_ITEMS: NavItem[] = ([
  { href: "/", label: "Home", icon: Home, mobile: true },
  { href: "/news", label: "News", icon: Newspaper, mobile: false },
  { href: "/originals", label: "Ideas", icon: BookOpen, mobile: false },
  { href: "/venues", label: "Places", icon: MapPinned, mobile: true },
  { href: "/deals", label: "Deals", icon: Tag, mobile: false },
  { href: "/events", label: "Events", icon: CalendarHeart, mobile: true },
  { href: "/activities", label: "Activities", icon: Dumbbell, mobile: true },
  { href: "/forum", label: "Forum", icon: MessagesSquare, mobile: false },
  { href: "/ops", label: "Operations", icon: Settings, mobile: false },
  { href: "/profile", label: "Profile", icon: UserRound, mobile: false },
] satisfies NavItem[]).filter(item => item.href !== "/forum" || FORUM_ENABLED)

export function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href)
}

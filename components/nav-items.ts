import { BookOpen, CalendarHeart, Dumbbell, Home, MapPinned, MessagesSquare, Newspaper, Tag, UserRound, type LucideIcon } from "lucide-react"
import { FORUM_ENABLED } from "@/lib/launch"

export type NavItem = { href: string; label: string; icon: LucideIcon; mobile: boolean }

export const NAV_ITEMS: NavItem[] = ([
  { href: "/", label: "Home", icon: Home, mobile: true },
  { href: "/news", label: "News", icon: Newspaper, mobile: true },
  { href: "/originals", label: "Originals", icon: BookOpen, mobile: true },
  { href: "/venues", label: "Venues", icon: MapPinned, mobile: true },
  { href: "/deals", label: "Deals", icon: Tag, mobile: true },
  { href: "/events", label: "Events", icon: CalendarHeart, mobile: false },
  { href: "/activities", label: "Activities", icon: Dumbbell, mobile: true },
  { href: "/forum", label: "Forum", icon: MessagesSquare, mobile: true },
  { href: "/profile", label: "Profile", icon: UserRound, mobile: false },
] satisfies NavItem[]).filter(item => item.href !== "/forum" || FORUM_ENABLED)

export function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href)
}

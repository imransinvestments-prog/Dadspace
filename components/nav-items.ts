import { CalendarHeart, Dumbbell, Home, MapPinned, MessagesSquare, Newspaper, Tag, UserRound, type LucideIcon } from "lucide-react"

export type NavItem = { href: string; label: string; icon: LucideIcon; mobile: boolean }

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Home", icon: Home, mobile: true },
  { href: "/news", label: "News", icon: Newspaper, mobile: true },
  { href: "/venues", label: "Venues", icon: MapPinned, mobile: false },
  { href: "/deals", label: "Deals", icon: Tag, mobile: true },
  { href: "/events", label: "Events", icon: CalendarHeart, mobile: true },
  { href: "/activities", label: "Activities", icon: Dumbbell, mobile: false },
  { href: "/forum", label: "Forum", icon: MessagesSquare, mobile: true },
  { href: "/profile", label: "Profile", icon: UserRound, mobile: false },
]

export function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href)
}

import type { Metadata } from "next"
import { ComingSoon } from "@/components/coming-soon"

export const metadata: Metadata = { title: "Forum" }

export default function ForumPage() {
  return <ComingSoon title="Forum" joke="The dad chat is being set up. Please hold, your call is important to us (and so are your puns)." />
}

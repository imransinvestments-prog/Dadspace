import { ComingSoon } from "@/components/coming-soon"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Dad Forum",
  "/forum",
  "A UK community space for dads to talk parenting, family life, rights, money, relationships and everything in between.",
  { noIndex: true },
)

export default function ForumPage() {
  return <ComingSoon title="Forum" joke="The dad chat is being set up. Please hold, your call is important to us (and so are your puns)." />
}

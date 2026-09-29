import type { Metadata } from "next"
import { ComingSoon } from "@/components/coming-soon"

export const metadata: Metadata = { title: "News" }

export default function NewsPage() {
  return <ComingSoon title="News" joke="Topic filters and save-for-later are coming. In the meantime, the headlines are on Home." />
}

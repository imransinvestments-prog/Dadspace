import type { Metadata } from "next"
import { ComingSoon } from "@/components/coming-soon"

export const metadata: Metadata = { title: "Deals" }

export default function DealsPage() {
  return <ComingSoon title="Deals" joke="We're hunting down bargains on buggies and nappies. Unlike your car keys, these we'll actually find." />
}

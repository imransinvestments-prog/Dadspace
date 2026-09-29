import type { Metadata } from "next"
import { ComingSoon } from "@/components/coming-soon"

export const metadata: Metadata = { title: "Profile" }

export default function ProfilePage() {
  return <ComingSoon title="Your profile" joke="Sign-up, saved items and preferences are next. For now you're an international dad of mystery." />
}

import type { Metadata } from "next"
import Link from "next/link"
import { AuthLayout } from "@/components/auth/auth-layout"

export const metadata: Metadata = { title: "Link problem", robots: { index: false, follow: false } }

export default function AuthErrorPage() {
  return (
    <AuthLayout
      eyebrow="Well, that didn't work"
      title="That link has expired"
      intro="Sign-in and email links only work once and run out after a while. Try logging in again, or ask for a fresh link."
    >
      <div className="flex flex-col gap-3 sm:flex-row">
        <Link href="/auth/login" className="inline-flex h-12 flex-1 items-center justify-center rounded-full bg-primary px-6 font-semibold text-primary-foreground">
          Log in
        </Link>
        <Link href="/auth/forgot-password" className="inline-flex h-12 flex-1 items-center justify-center rounded-full border px-6 font-semibold transition hover:bg-muted">
          Reset password
        </Link>
      </div>
    </AuthLayout>
  )
}

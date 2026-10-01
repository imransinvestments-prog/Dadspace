import type { Metadata } from "next"
import Link from "next/link"
import { MailCheck } from "lucide-react"
import { AuthLayout } from "@/components/auth/auth-layout"

export const metadata: Metadata = { title: "Check your email", robots: { index: false, follow: false } }

export default function SignUpSuccessPage() {
  return (
    <AuthLayout eyebrow="Nearly there" title="Check your email" intro="We've sent you a link to confirm your account. Click it and you'll land back here, logged in.">
      <div className="flex items-start gap-4 rounded-xl bg-muted p-5">
        <MailCheck className="mt-0.5 size-6 shrink-0 text-primary" aria-hidden />
        <p className="text-sm leading-relaxed text-muted-foreground">
          Nothing after a couple of minutes? Check your spam or promotions folder. The link expires after 24 hours.
        </p>
      </div>
      <Link href="/" className="inline-flex h-12 items-center justify-center rounded-full border px-6 font-semibold transition hover:bg-muted">
        Back to Home
      </Link>
    </AuthLayout>
  )
}

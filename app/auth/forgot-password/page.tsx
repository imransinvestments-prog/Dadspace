import type { Metadata } from "next"
import { AuthLayout } from "@/components/auth/auth-layout"
import { ForgotPasswordForm } from "@/components/auth/forgot-password-form"

export const metadata: Metadata = { title: "Forgot password", robots: { index: false, follow: true } }

export default function ForgotPasswordPage() {
  return (
    <AuthLayout eyebrow="It happens" title="Forgot your password?" intro="Pop your email in and we'll send you a link to set a new one.">
      <ForgotPasswordForm />
    </AuthLayout>
  )
}

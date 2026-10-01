import type { Metadata } from "next"
import { AuthLayout } from "@/components/auth/auth-layout"
import { LoginForm } from "@/components/auth/login-form"
import { safeNext } from "@/lib/auth/redirect"

export const metadata: Metadata = {
  title: "Log in",
  description: "Log in to your Dadspace account.",
  robots: { index: false, follow: true },
  alternates: { canonical: "/auth/login" },
}

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams
  const destination = safeNext(next)
  const notice = destination !== "/" ? "Log in or create a free account to see that page." : undefined

  return (
    <AuthLayout eyebrow="Welcome back" title="Log in to Dadspace" intro="Good to see you again. The kettle's on.">
      <LoginForm next={destination} notice={notice} />
    </AuthLayout>
  )
}

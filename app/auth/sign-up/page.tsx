import type { Metadata } from "next"
import { AuthLayout } from "@/components/auth/auth-layout"
import { SignUpForm } from "@/components/auth/sign-up-form"
import { safeNext } from "@/lib/auth/redirect"

export const metadata: Metadata = {
  title: "Sign up",
  description: "Create a free Dadspace account to join the chat and save your favourite days out.",
  robots: { index: false, follow: true },
  alternates: { canonical: "/auth/sign-up" },
}

export default async function SignUpPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams

  return (
    <AuthLayout eyebrow="Join the squad" title="Create your free account" intro="It takes less time than finding a matching pair of kids' socks.">
      <SignUpForm next={safeNext(next)} />
    </AuthLayout>
  )
}

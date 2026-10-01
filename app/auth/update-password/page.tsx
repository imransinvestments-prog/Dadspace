import type { Metadata } from "next"
import Link from "next/link"
import { AuthLayout } from "@/components/auth/auth-layout"
import { UpdatePasswordForm } from "@/components/auth/update-password-form"
import { FormMessage } from "@/components/auth/form-parts"
import { createClient } from "@/lib/supabase/server"

export const metadata: Metadata = { title: "Set a new password", robots: { index: false, follow: false } }

export default async function UpdatePasswordPage() {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  return (
    <AuthLayout eyebrow="Fresh start" title="Set a new password" intro="Choose something you'll remember, but the kids won't guess.">
      {user ? (
        <UpdatePasswordForm />
      ) : (
        <div className="flex flex-col gap-4">
          <FormMessage>That reset link has expired or was already used. Request a new one and use it within the hour.</FormMessage>
          <Link href="/auth/forgot-password" className="inline-flex h-12 items-center justify-center rounded-full bg-primary px-6 font-semibold text-primary-foreground">
            Send a new link
          </Link>
        </div>
      )}
    </AuthLayout>
  )
}

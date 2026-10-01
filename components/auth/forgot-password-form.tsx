"use client"

import Link from "next/link"
import { useState } from "react"
import { createClient } from "@/lib/supabase/client"
import { authCallbackUrl } from "@/lib/auth/redirect"
import { Field, FormMessage, SubmitButton, authErrorMessage } from "./form-parts"

export function ForgotPasswordForm() {
  const [error, setError] = useState<string | null>(null)
  const [sent, setSent] = useState(false)
  const [pending, setPending] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const email = String(new FormData(event.currentTarget).get("email")).trim()
    setPending(true)
    setError(null)

    const { error } = await createClient().auth.resetPasswordForEmail(email, {
      redirectTo: authCallbackUrl("/auth/update-password"),
    })
    setPending(false)

    // Unknown emails succeed silently in Supabase, so this never reveals who has an account.
    if (error) {
      console.error("Password reset error:", error.code ?? error.message)
      setError(authErrorMessage(error))
      return
    }
    setSent(true)
  }

  if (sent) {
    return (
      <div className="flex flex-col gap-4">
        <FormMessage tone="success">
          If that email has a Dadspace account, a reset link is on its way. It can take a minute or two, so check your spam folder too.
        </FormMessage>
        <Link href="/auth/login" className="text-sm font-semibold text-primary underline-offset-4 hover:underline">
          Back to log in
        </Link>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Field id="email" name="email" type="email" label="Email" autoComplete="email" required placeholder="you@example.com" />
      {error && <FormMessage>{error}</FormMessage>}
      <SubmitButton pending={pending} pendingLabel="Sending…">
        Send reset link
      </SubmitButton>
      <Link href="/auth/login" className="text-center text-sm font-semibold text-primary underline-offset-4 hover:underline">
        Remembered it? Log in
      </Link>
    </form>
  )
}

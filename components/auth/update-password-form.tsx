"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { createClient } from "@/lib/supabase/client"
import { Field, FormMessage, SubmitButton, authErrorMessage } from "./form-parts"

export function UpdatePasswordForm() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const password = String(form.get("password"))

    if (password.length < 8) {
      setError("Your password needs at least 8 characters.")
      return
    }
    if (password !== String(form.get("confirmPassword"))) {
      setError("Those two passwords don't match.")
      return
    }

    setPending(true)
    setError(null)
    const { error } = await createClient().auth.updateUser({ password })
    if (error) {
      console.error("Update password error:", error.code ?? error.message)
      setError(authErrorMessage(error))
      setPending(false)
      return
    }
    router.replace("/profile?updated=password")
    router.refresh()
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Field id="password" name="password" type="password" label="New password" autoComplete="new-password" required minLength={8} hint="At least 8 characters." />
      <Field id="confirmPassword" name="confirmPassword" type="password" label="Confirm new password" autoComplete="new-password" required minLength={8} />
      {error && <FormMessage>{error}</FormMessage>}
      <SubmitButton pending={pending} pendingLabel="Saving…">
        Save new password
      </SubmitButton>
    </form>
  )
}

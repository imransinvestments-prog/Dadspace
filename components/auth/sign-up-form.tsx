"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { createClient } from "@/lib/supabase/client"
import { authCallbackUrl } from "@/lib/auth/redirect"
import { Field, FormMessage, OrDivider, SubmitButton, authErrorMessage } from "./form-parts"
import { GoogleButton } from "./google-button"

export function SignUpForm({ next }: { next: string }) {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const displayName = String(form.get("displayName")).trim()
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
    const { data, error } = await createClient().auth.signUp({
      email: String(form.get("email")).trim(),
      password,
      options: {
        emailRedirectTo: authCallbackUrl(next),
        data: { display_name: displayName },
      },
    })

    if (error) {
      console.error("Sign-up error:", error.code ?? error.message)
      setError(authErrorMessage(error))
      setPending(false)
      return
    }

    if (data.session) {
      router.replace(next)
      router.refresh()
    } else {
      router.push("/auth/sign-up-success")
    }
  }

  const loginHref = next === "/" ? "/auth/login" : `/auth/login?next=${encodeURIComponent(next)}`

  return (
    <div className="flex flex-col gap-5">
      <GoogleButton next={next} onError={setError} />
      <OrDivider />
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field
          id="displayName"
          name="displayName"
          label="Display name"
          autoComplete="nickname"
          required
          maxLength={40}
          placeholder="Dave from Didsbury"
          hint="This is what other dads see. You can change it later."
        />
        <Field id="email" name="email" type="email" label="Email" autoComplete="email" required placeholder="you@example.com" />
        <Field id="password" name="password" type="password" label="Password" autoComplete="new-password" required minLength={8} hint="At least 8 characters." />
        <Field id="confirmPassword" name="confirmPassword" type="password" label="Confirm password" autoComplete="new-password" required minLength={8} />
        {error && <FormMessage>{error}</FormMessage>}
        <SubmitButton pending={pending} pendingLabel="Creating account…">
          Create account
        </SubmitButton>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        Already one of us?{" "}
        <Link href={loginHref} className="font-semibold text-primary underline-offset-4 hover:underline">
          Log in
        </Link>
      </p>
    </div>
  )
}

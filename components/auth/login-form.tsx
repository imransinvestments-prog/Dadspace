"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { createClient } from "@/lib/supabase/client"
import { Field, FormMessage, OrDivider, SubmitButton, authErrorMessage } from "./form-parts"
import { GoogleButton } from "./google-button"

export function LoginForm({ next, notice }: { next: string; notice?: string }) {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setPending(true)
    setError(null)

    const { error } = await createClient().auth.signInWithPassword({
      email: String(form.get("email")).trim(),
      password: String(form.get("password")),
    })

    if (error) {
      console.error("Login error:", error.code ?? error.message)
      setError(authErrorMessage(error))
      setPending(false)
      return
    }
    router.replace(next)
    router.refresh()
  }

  const signUpHref = next === "/" ? "/auth/sign-up" : `/auth/sign-up?next=${encodeURIComponent(next)}`

  return (
    <div className="flex flex-col gap-5">
      {notice && <FormMessage tone="success">{notice}</FormMessage>}
      <GoogleButton next={next} onError={setError} />
      <OrDivider />
      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate={false}>
        <Field id="email" name="email" type="email" label="Email" autoComplete="email" required placeholder="you@example.com" />
        <Field id="password" name="password" type="password" label="Password" autoComplete="current-password" required />
        <Link href="/auth/forgot-password" className="-mt-1 self-end text-sm font-semibold text-primary underline-offset-4 hover:underline">
          Forgot your password?
        </Link>
        {error && <FormMessage>{error}</FormMessage>}
        <SubmitButton pending={pending} pendingLabel="Logging in…">
          Log in
        </SubmitButton>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        New here?{" "}
        <Link href={signUpHref} className="font-semibold text-primary underline-offset-4 hover:underline">
          Create an account
        </Link>
      </p>
    </div>
  )
}

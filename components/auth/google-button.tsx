"use client"

import { useState } from "react"
import { Loader2 } from "lucide-react"
import { createClient } from "@/lib/supabase/client"
import { authCallbackUrl } from "@/lib/auth/redirect"

export function GoogleButton({ next, onError }: { next: string; onError: (message: string) => void }) {
  const [pending, setPending] = useState(false)

  async function handleClick() {
    setPending(true)
    const { error } = await createClient().auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: authCallbackUrl(next) },
    })
    if (error) {
      console.error("Google sign-in error:", error.code ?? error.message)
      onError("Google sign-in isn't available right now. Please use your email instead.")
      setPending(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={pending}
      className="inline-flex h-12 items-center justify-center gap-3 rounded-full border bg-background px-6 font-semibold transition hover:bg-muted disabled:opacity-60"
    >
      {pending ? <Loader2 className="size-5 animate-spin" aria-hidden /> : <GoogleMark />}
      Continue with Google
    </button>
  )
}

function GoogleMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-5" aria-hidden>
      <path fill="#4285F4" d="M23.5 12.27c0-.85-.08-1.67-.22-2.45H12v4.64h6.45a5.52 5.52 0 0 1-2.39 3.62v3h3.87c2.26-2.09 3.57-5.16 3.57-8.81Z" />
      <path fill="#34A853" d="M12 24c3.24 0 5.95-1.07 7.93-2.92l-3.87-3c-1.07.72-2.45 1.15-4.06 1.15-3.12 0-5.77-2.11-6.71-4.95h-4v3.1A11.99 11.99 0 0 0 12 24Z" />
      <path fill="#FBBC05" d="M5.29 14.28a7.2 7.2 0 0 1 0-4.56v-3.1h-4a12 12 0 0 0 0 10.76l4-3.1Z" />
      <path fill="#EA4335" d="M12 4.77c1.76 0 3.34.61 4.59 1.8l3.43-3.43A11.97 11.97 0 0 0 1.29 6.62l4 3.1C6.23 6.88 8.88 4.77 12 4.77Z" />
    </svg>
  )
}

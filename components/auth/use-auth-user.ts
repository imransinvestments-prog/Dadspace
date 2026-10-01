"use client"

import { useEffect, useState } from "react"
import type { User } from "@supabase/supabase-js"
import { createClient } from "@/lib/supabase/client"

export type AuthUserSummary = { id: string; displayName: string; avatarUrl: string | null }

function summarise(user: User): AuthUserSummary {
  const meta = user.user_metadata ?? {}
  const displayName = String(meta.display_name || meta.full_name || meta.name || user.email?.split("@")[0] || "Dad").slice(0, 40)
  const avatarUrl = typeof (meta.avatar_url || meta.picture) === "string" ? meta.avatar_url || meta.picture : null
  return { id: user.id, displayName, avatarUrl }
}

/** `undefined` while the session is loading, `null` when signed out. Updates live on log in/out and profile edits. */
export function useAuthUser() {
  const [user, setUser] = useState<AuthUserSummary | null | undefined>(undefined)

  useEffect(() => {
    if (!process.env.NEXT_PUBLIC_DADSPACE_SUPABASE_URL) {
      setUser(null)
      return
    }
    const {
      data: { subscription },
    } = createClient().auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ? summarise(session.user) : null)
    })
    return () => subscription.unsubscribe()
  }, [])

  return user
}

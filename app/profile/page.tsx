import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { createClient } from "@/lib/supabase/server"
import { ProfileForm } from "@/components/auth/profile-form"
import { LogOutButton } from "@/components/auth/user-menu"
import { FormMessage } from "@/components/auth/form-parts"

export const metadata: Metadata = { title: "Your profile", robots: { index: false, follow: false } }

const joinedFormat = new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric" })

export default async function ProfilePage({ searchParams }: { searchParams: Promise<{ updated?: string }> }) {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()
  if (!user) redirect("/auth/login?next=/profile")

  const { data: profile, error } = await supabase
    .from("profiles")
    .select("display_name, avatar_url, created_at")
    .eq("id", user.id)
    .maybeSingle()
  if (error) console.error("Profile load error:", error.code ?? error.message)

  const meta = user.user_metadata ?? {}
  const displayName = profile?.display_name || meta.display_name || meta.full_name || user.email?.split("@")[0] || ""
  const avatarUrl = profile?.avatar_url || meta.avatar_url || meta.picture || null
  const joined = joinedFormat.format(new Date(profile?.created_at ?? user.created_at))
  const viaGoogle = user.app_metadata?.provider === "google"
  const { updated } = await searchParams

  return (
    <section className="animate-rise flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <p className="text-sm font-semibold tracking-wide text-accent uppercase">Your profile</p>
        <h1 className="font-heading text-4xl font-extrabold tracking-tight text-balance">Alright, {displayName || "Dad"}?</h1>
        <p className="text-muted-foreground">Member since {joined}</p>
      </header>

      {updated === "password" && <FormMessage tone="success">Your password has been changed.</FormMessage>}

      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="rounded-xl border bg-card p-6 sm:p-8">
          <h2 className="mb-6 font-heading text-xl font-bold">How other dads see you</h2>
          <ProfileForm userId={user.id} displayName={displayName} avatarUrl={avatarUrl} />
        </div>

        <aside className="flex flex-col gap-4 rounded-xl border bg-card p-6">
          <h2 className="font-heading text-xl font-bold">Account</h2>
          <dl className="flex flex-col gap-3 text-sm">
            <div className="flex flex-col gap-0.5">
              <dt className="text-muted-foreground">Email</dt>
              <dd className="font-semibold break-all">{user.email}</dd>
            </div>
            <div className="flex flex-col gap-0.5">
              <dt className="text-muted-foreground">Signed in with</dt>
              <dd className="font-semibold">{viaGoogle ? "Google" : "Email and password"}</dd>
            </div>
          </dl>
          {!viaGoogle && (
            <a href="/auth/update-password" className="text-sm font-semibold text-primary underline-offset-4 hover:underline">
              Change password
            </a>
          )}
          <div className="mt-auto pt-2">
            <LogOutButton />
          </div>
        </aside>
      </div>
    </section>
  )
}

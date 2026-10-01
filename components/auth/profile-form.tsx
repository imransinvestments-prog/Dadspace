"use client"

import { useRouter } from "next/navigation"
import { useRef, useState } from "react"
import { Camera, Loader2 } from "lucide-react"
import { createClient } from "@/lib/supabase/client"
import { Avatar } from "./user-menu"
import { Field, FormMessage, SubmitButton } from "./form-parts"

const MAX_AVATAR_BYTES = 2 * 1024 * 1024
const AVATAR_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]

export function ProfileForm({ userId, displayName, avatarUrl }: { userId: string; displayName: string; avatarUrl: string | null }) {
  const router = useRouter()
  const fileInput = useRef<HTMLInputElement>(null)
  const [name, setName] = useState(displayName)
  const [avatar, setAvatar] = useState(avatarUrl)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState<{ tone: "error" | "success"; text: string } | null>(null)

  async function saveProfile(fields: { display_name?: string; avatar_url?: string | null }) {
    const supabase = createClient()
    const { error } = await supabase.from("profiles").upsert({ id: userId, ...fields, updated_at: new Date().toISOString() })
    if (error) throw error
    // Mirror onto the account so the sidebar and header update straight away.
    await supabase.auth.updateUser({ data: fields })
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) {
      setMessage({ tone: "error", text: "Your display name can't be empty." })
      return
    }
    setSaving(true)
    setMessage(null)
    try {
      await saveProfile({ display_name: trimmed })
      setMessage({ tone: "success", text: "Saved. Looking good." })
      router.refresh()
    } catch (error) {
      console.error("Profile save error:", error)
      setMessage({ tone: "error", text: "We couldn't save that just now. Please try again." })
    } finally {
      setSaving(false)
    }
  }

  async function handleAvatar(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = ""
    if (!file) return
    if (!AVATAR_TYPES.includes(file.type)) {
      setMessage({ tone: "error", text: "Please choose a JPG, PNG, WebP or GIF image." })
      return
    }
    if (file.size > MAX_AVATAR_BYTES) {
      setMessage({ tone: "error", text: "That image is over 2 MB. Please choose a smaller one." })
      return
    }

    setUploading(true)
    setMessage(null)
    try {
      const supabase = createClient()
      const extension = file.type.split("/")[1].replace("jpeg", "jpg")
      const path = `${userId}/avatar-${Date.now()}.${extension}`
      const { error: uploadError } = await supabase.storage.from("avatars").upload(path, file, { contentType: file.type, upsert: true })
      if (uploadError) throw uploadError

      const publicUrl = supabase.storage.from("avatars").getPublicUrl(path).data.publicUrl
      await saveProfile({ avatar_url: publicUrl })
      setAvatar(publicUrl)
      setMessage({ tone: "success", text: "New photo saved." })
      router.refresh()
    } catch (error) {
      console.error("Avatar upload error:", error)
      setMessage({ tone: "error", text: "We couldn't upload that photo. Please try again." })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-5">
        <div className="relative">
          <Avatar user={{ displayName: name || displayName, avatarUrl: avatar }} className="size-24 text-4xl" />
          {uploading && (
            <span className="absolute inset-0 flex items-center justify-center rounded-full bg-background/70">
              <Loader2 className="size-6 animate-spin" aria-hidden />
            </span>
          )}
        </div>
        <div className="flex flex-col gap-2">
          <input ref={fileInput} type="file" accept={AVATAR_TYPES.join(",")} className="sr-only" onChange={handleAvatar} aria-label="Upload a profile photo" tabIndex={-1} />
          <button
            type="button"
            onClick={() => fileInput.current?.click()}
            disabled={uploading}
            className="inline-flex h-11 items-center gap-2 self-start rounded-full border px-5 text-sm font-semibold transition hover:bg-muted disabled:opacity-60"
          >
            <Camera className="size-4" aria-hidden />
            {avatar ? "Change photo" : "Add a photo"}
          </button>
          <p className="text-xs text-muted-foreground">JPG, PNG, WebP or GIF, up to 2 MB.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field
          id="displayName"
          name="displayName"
          label="Display name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={40}
          required
          autoComplete="nickname"
          hint="Shown next to anything you post."
        />
        {message && <FormMessage tone={message.tone}>{message.text}</FormMessage>}
        <SubmitButton pending={saving} pendingLabel="Saving…">
          Save changes
        </SubmitButton>
      </form>
    </div>
  )
}

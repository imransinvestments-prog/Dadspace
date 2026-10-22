import { CircleAlert, CircleCheck, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function Field({
  label,
  hint,
  id,
  errorId,
  ...input
}: React.InputHTMLAttributes<HTMLInputElement> & { id: string; label: string; hint?: string; errorId?: string }) {
  const describedBy = [hint && `${id}-hint`, input["aria-invalid"] && errorId].filter(Boolean).join(" ")
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-semibold">
        {label}
      </label>
      <input
        id={id}
        aria-describedby={describedBy || undefined}
        className="h-12 rounded-xl border bg-background px-4 text-base outline-none transition placeholder:text-muted-foreground focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-ring/40 aria-invalid:border-destructive"
        {...input}
      />
      {hint && (
        <p id={`${id}-hint`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      )}
    </div>
  )
}

export function SubmitButton({ pending, children, pendingLabel }: { pending: boolean; children: React.ReactNode; pendingLabel: string }) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex h-12 items-center justify-center gap-2 rounded-full bg-primary px-6 font-semibold text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
    >
      {pending && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {pending ? pendingLabel : children}
    </button>
  )
}

export function FormMessage({ tone = "error", id, children }: { tone?: "error" | "success"; id?: string; children: React.ReactNode }) {
  const Icon = tone === "error" ? CircleAlert : CircleCheck
  return (
    <p
      id={id}
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "flex items-start gap-2 rounded-xl border px-4 py-3 text-sm leading-relaxed",
        tone === "error" ? "border-destructive/50 bg-destructive/10" : "border-primary/40 bg-primary/10",
      )}
    >
      <Icon className={cn("mt-0.5 size-4 shrink-0", tone === "error" ? "text-destructive" : "text-primary-ink")} aria-hidden />
      <span>{children}</span>
    </p>
  )
}

export function OrDivider() {
  return (
    <div className="flex items-center gap-3 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
      <span className="h-px flex-1 bg-border" />
      or
      <span className="h-px flex-1 bg-border" />
    </div>
  )
}

/** Only the "wrong email/password" signal is generic; anything the user can act on is passed through. */
export function authErrorMessage(error: unknown): string {
  const { code, status } = (error ?? {}) as { code?: string; status?: number }
  switch (code) {
    case "email_not_confirmed":
      return "Please confirm your email first. Check your inbox (and spam) for the link."
    case "invalid_credentials":
      return "That email and password don't match. Have another go."
    case "weak_password":
      return "That password is too easy to guess. Use at least 8 characters with a mix of letters and numbers."
    case "same_password":
      return "Your new password needs to be different from the old one."
    case "email_address_invalid":
      return "That email address doesn't look right."
    case "signup_disabled":
      return "New sign-ups are switched off at the moment."
    case "over_email_send_rate_limit":
      return "We've sent too many emails recently. Please wait a few minutes and try again."
  }
  if (code === "over_request_rate_limit" || status === 429) return "Too many attempts. Please wait a moment and try again."
  return "Something went wrong on our side. Please try again."
}

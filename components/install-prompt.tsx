"use client"

import { Download, Share, X } from "lucide-react"
import { useEffect, useState } from "react"

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>
}

export function InstallPrompt({ variant }: { variant: "card" | "banner" }) {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null)
  const [isIos, setIsIos] = useState(false)
  const [dismissed, setDismissed] = useState(true)

  useEffect(() => {
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (navigator as Navigator & { standalone?: boolean }).standalone === true
    if (standalone || sessionStorage.getItem("ds-install-dismissed")) return

    setDismissed(false)
    setIsIos(/iphone|ipad|ipod/i.test(navigator.userAgent))

    const onPrompt = (e: Event) => {
      e.preventDefault()
      setDeferred(e as BeforeInstallPromptEvent)
    }
    const onInstalled = () => setDismissed(true)
    window.addEventListener("beforeinstallprompt", onPrompt)
    window.addEventListener("appinstalled", onInstalled)
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt)
      window.removeEventListener("appinstalled", onInstalled)
    }
  }, [])

  if (dismissed || (!deferred && !isIos)) return null

  const dismiss = () => {
    sessionStorage.setItem("ds-install-dismissed", "1")
    setDismissed(true)
  }

  const install = async () => {
    if (!deferred) return
    await deferred.prompt()
    await deferred.userChoice
    setDeferred(null)
    setDismissed(true)
  }

  const message = isIos ? (
    <>
      Tap <Share className="inline size-4 align-text-bottom" aria-label="Share" /> then &quot;Add to Home Screen&quot;.
    </>
  ) : (
    "One tap, no app store. Like a dad shortcut."
  )

  if (variant === "card") {
    return (
      <div className="relative flex flex-col gap-3 rounded-lg bg-navy p-4 text-navy-foreground">
        <button type="button" onClick={dismiss} className="absolute top-2 right-2 rounded-full p-1.5 hover:bg-card/10" aria-label="Dismiss install prompt">
          <X className="size-4" aria-hidden />
        </button>
        <p className="pr-6 font-heading text-base font-bold">Pop Dadspace on your phone</p>
        <p className="text-sm leading-relaxed text-navy-foreground/80">{message}</p>
        {deferred && (
          <button type="button" onClick={install} className="inline-flex h-11 items-center justify-center gap-2 rounded-full bg-primary font-semibold text-primary-foreground">
            <Download className="size-4" aria-hidden />
            Install app
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3 rounded-lg bg-navy p-3 pl-4 text-navy-foreground">
      <p className="flex-1 text-sm leading-relaxed">
        <span className="font-semibold">Add Dadspace to your home screen.</span> <span className="text-navy-foreground/80">{message}</span>
      </p>
      {deferred && (
        <button type="button" onClick={install} className="h-11 shrink-0 rounded-full bg-primary px-4 text-sm font-semibold text-primary-foreground">
          Install
        </button>
      )}
      <button type="button" onClick={dismiss} className="shrink-0 rounded-full p-2 hover:bg-card/10" aria-label="Dismiss install prompt">
        <X className="size-4" aria-hidden />
      </button>
    </div>
  )
}

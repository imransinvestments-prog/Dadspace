"use client"

import { useCallback, useState } from "react"
import { isRegion, type RegionFilter } from "@/lib/news"

type Status = "idle" | "locating" | "error"

const MESSAGES = {
  unsupported: "Your browser can't share its location. Pick a region instead.",
  insecure: "Location only works on the live (https) site. Pick a region instead.",
  denied: "Location is blocked for this site. Allow it in your browser settings, or pick a region.",
  unavailable: "We couldn't get a fix on your location. Try again, or pick a region.",
  outside: "Looks like you're outside the UK nations we cover, so we've kept All UK.",
  failed: "We couldn't work out your region just now. Try again, or pick one.",
} as const

function getPosition(): Promise<GeolocationPosition> {
  return new Promise((resolve, reject) =>
    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: false,
      timeout: 15000,
      maximumAge: 60 * 60 * 1000,
    }),
  )
}

/** Asks the browser for its location and maps it to a UK nation for the News filter. */
export function useRegionFromLocation(onRegion: (region: RegionFilter) => void) {
  const [status, setStatus] = useState<Status>("idle")
  const [message, setMessage] = useState<string | null>(null)

  const locate = useCallback(async () => {
    setMessage(null)
    if (!("geolocation" in navigator)) return fail(MESSAGES.unsupported)
    if (!window.isSecureContext) return fail(MESSAGES.insecure)

    setStatus("locating")
    let position: GeolocationPosition
    try {
      position = await getPosition()
    } catch (err) {
      const code = (err as GeolocationPositionError).code
      return fail(code === 1 ? MESSAGES.denied : MESSAGES.unavailable)
    }

    try {
      const { latitude, longitude } = position.coords
      const res = await fetch(`/api/region?lat=${latitude}&lng=${longitude}`)
      if (!res.ok) return fail(MESSAGES.failed)
      const { region } = (await res.json()) as { region: string | null }
      if (!isRegion(region) || region === "all") return fail(MESSAGES.outside)
      onRegion(region)
      setStatus("idle")
    } catch {
      fail(MESSAGES.failed)
    }

    function fail(text: string) {
      setStatus("error")
      setMessage(text)
    }
  }, [onRegion])

  return { locate, status, message }
}

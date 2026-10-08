"use client"

import { useCallback, useState } from "react"
import { parseNewsLocation, type NewsLocation } from "@/lib/news"
import { parsePoint } from "@/lib/distance"

type Status = "idle" | "locating" | "error"

const MESSAGES = {
  unsupported: "Your browser can't share its location. Pick a region instead.",
  insecure: "Location only works on the live (https) site. Pick a region instead.",
  denied: "Location is blocked for this site. Allow it in your browser settings, or pick a region.",
  unavailable: "We couldn't get a fix on your location. Try again, or pick a region.",
  outside: "Looks like you're outside the UK nations we cover, so we've kept All UK.",
  failed: "We couldn't work out your area just now. Try again, or pick a region.",
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

/** Asks the browser for its location and maps it to coarse UK news geography. */
export function useRegionFromLocation(onLocation: (location: NewsLocation) => void) {
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
      const point = parsePoint(new URLSearchParams({ lat: String(position.coords.latitude), lng: String(position.coords.longitude) }))
      if (!point) return fail(MESSAGES.unavailable)
      const res = await fetch(`/api/region?lat=${point.lat}&lng=${point.lng}`)
      if (!res.ok) return fail(MESSAGES.failed)
      const result = parseNewsLocation(await res.json())
      if (!result) return fail(MESSAGES.outside)
      onLocation(result)
      setStatus("idle")
    } catch {
      fail(MESSAGES.failed)
    }

    function fail(text: string) {
      setStatus("error")
      setMessage(text)
    }
  }, [onLocation])

  return { locate, status, message }
}

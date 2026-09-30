"use client"

import { createContext, useCallback, useContext, useEffect, useState } from "react"

export type Coords = { lat: number; lng: number }
export type LocationStatus = "idle" | "locating" | "ready" | "denied" | "unavailable"

type LocationContextValue = { coords: Coords | null; status: LocationStatus; request: () => void }

const LocationContext = createContext<LocationContextValue>({ coords: null, status: "idle", request: () => {} })

const round = (n: number) => Math.round(n * 100) / 100

/** Asks for the device location once when the app opens and shares it (rounded to ~1km) with the pages. */
export function LocationProvider({ children }: { children: React.ReactNode }) {
  const [coords, setCoords] = useState<Coords | null>(null)
  const [status, setStatus] = useState<LocationStatus>("idle")

  const request = useCallback(() => {
    if (!("geolocation" in navigator) || !window.isSecureContext) {
      setStatus("unavailable")
      return
    }
    setStatus("locating")
    navigator.geolocation.getCurrentPosition(
      ({ coords: c }) => {
        setCoords({ lat: round(c.latitude), lng: round(c.longitude) })
        setStatus("ready")
      },
      (err) => setStatus(err.code === err.PERMISSION_DENIED ? "denied" : "unavailable"),
      { enableHighAccuracy: false, timeout: 15000, maximumAge: 30 * 60 * 1000 },
    )
  }, [])

  useEffect(() => {
    request()
  }, [request])

  return <LocationContext.Provider value={{ coords, status, request }}>{children}</LocationContext.Provider>
}

export const useLocation = () => useContext(LocationContext)

"use client"

import { createContext, useCallback, useContext, useState } from "react"
import { parsePoint } from "@/lib/distance"
import { TEST_LOCATION } from "@/lib/test-location"

export type Coords = { lat: number; lng: number }
export type LocationStatus = "idle" | "locating" | "ready" | "denied" | "unavailable"
type Value = { coords: Coords | null; status: LocationStatus; label: string; request: () => void; setLocation: (p: Coords, label?: string) => void; browseAll: boolean }
const LocationContext = createContext<Value>({
  coords: TEST_LOCATION.point, status: "ready", label: TEST_LOCATION.label,
  request: () => {}, setLocation: () => {}, browseAll: false,
})

// Testing branch only. The saved postcode replaces device geolocation.
// Every fresh visit uses the latest configured postcode, avoiding stale sessions.
export function LocationProvider({ children }: { children: React.ReactNode }) {
  const [coords, setCoords] = useState<Coords>(TEST_LOCATION.point)
  const [label, setLabel] = useState<string>(TEST_LOCATION.label)
  const setLocation = useCallback((p: Coords, name = "Selected destination") => {
    const point = parsePoint(new URLSearchParams({ lat: String(p.lat), lng: String(p.lng) }))
    if (!point) return
    setCoords(point)
    setLabel(name)
  }, [])
  const request = useCallback(() => {
    setLocation(TEST_LOCATION.point, TEST_LOCATION.label)
  }, [setLocation])
  return <LocationContext.Provider value={{ coords, status: "ready", label, request, setLocation, browseAll: false }}>
    {children}
  </LocationContext.Provider>
}

export const useLocation = () => useContext(LocationContext)

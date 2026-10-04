"use client"

import { useLocation } from "@/components/location-provider"

export function LocationControls() {
  const { status, label, request } = useLocation()

  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p role="status" className="text-sm font-semibold">
          Searching near {label} · nearest first
        </p>
        <button
          type="button"
          onClick={request}
          disabled={status === "locating"}
          className="rounded-full border px-3 py-2 text-sm font-semibold disabled:opacity-50"
        >
          {status === "locating" ? "Finding location…" : "Use my current location"}
        </button>
      </div>
      <p className="text-xs text-muted-foreground">
        Distances are approximate straight-line distances.
      </p>
      {(status === "denied" || status === "unavailable") && (
        <p role="alert" className="text-sm text-destructive">
          Could not use your device location. Your search area is unchanged. Check
          location permission and try again.
        </p>
      )}
    </div>
  )
}

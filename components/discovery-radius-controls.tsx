"use client"

import Link from 'next/link'
import { RADIUS_OPTIONS, type DiscoveryScope } from '@/lib/discovery-radius'

export function DiscoveryRadiusControls({ radiusKm, scope, onRadius, onScope }: {
  radiusKm: number; scope: DiscoveryScope; onRadius: (radius: number) => void; onScope: (scope: DiscoveryScope) => void
}) {
  const next = RADIUS_OPTIONS.find(value => value > radiusKm)
  return <div className="flex flex-wrap items-center gap-3 rounded-xl border bg-card p-4">
    <label className="flex min-w-0 max-w-full flex-col gap-2 sm:flex-row sm:items-center">Search radius
      <select aria-label="Search radius" value={radiusKm} onChange={event => onRadius(Number(event.target.value))} className="min-w-0 max-w-full rounded-lg border bg-background p-2">
        {RADIUS_OPTIONS.map(value => <option key={value} value={value}>{value} km</option>)}
      </select>
    </label>
    <label className="flex min-w-0 max-w-full flex-col gap-2 sm:flex-row sm:items-center">Listings
      <select aria-label="Listing location scope" value={scope} onChange={event => onScope(event.target.value as DiscoveryScope)} className="min-w-0 max-w-full rounded-lg border bg-background p-2">
        <option value="local">Within radius</option><option value="unknown">Distance unknown — separate listings</option><option value="online">Online — separate listings</option>
      </select>
    </label>
    {scope === 'local' && next && <button type="button" className="font-semibold underline" onClick={() => onRadius(next)}>Widen search to {next} km</button>}
    <p className="w-full text-sm text-muted-foreground">{scope === 'local' ? `Only listings within ${radiusKm} km. Distances are straight-line, not travel distances.` : scope === 'online' ? 'Online listings are separate from local matches.' : 'These listings have no confirmed distance and are not local matches.'}</p>
  </div>
}

export function LocalCoverageGap() {
  return <div className="rounded-xl border bg-card p-6 text-center">
    <p>No confirmed local listings match these filters in this radius yet. This is a gap in our coverage, rather than proof that nothing is available.</p>
    <p className="mt-3"><Link className="underline" href="/venues">Explore nearby places</Link>{' · '}<a className="underline" href="#ideas-at-home">Find ideas at home</a></p>
    <div id="ideas-at-home" className="mt-4 text-sm"><h3 className="font-semibold">Ideas at home</h3><p>Try a shared story, drawing together or an indoor treasure hunt. Choose materials and supervision appropriate to your child.</p></div>
  </div>
}

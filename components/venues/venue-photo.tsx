"use client"

import Image from "next/image"
import { useState } from "react"
import { categoryImage, categoryLabel, venuePhotoUrl, type Venue } from "@/lib/venue-meta"

/** Credits travel with the photo in both cards and the surprise-pick view. */
export function VenuePhoto({ venue, sizes, className }: { venue: Venue; sizes: string; className?: string }) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  const candidate = venuePhotoUrl(venue)
  const photo = candidate && candidate !== failedUrl ? candidate : null
  return (
    <>
      <Image
        src={photo ?? categoryImage(venue.category)}
        alt={photo ? `Photo of ${venue.name}` : `${categoryLabel(venue.category)} illustration, not a photo of this venue`}
        fill
        unoptimized={Boolean(photo)}
        sizes={sizes}
        className={className}
        onError={() => { if (photo) setFailedUrl(photo) }}
      />
      <div className="absolute inset-x-0 bottom-0 z-10 bg-black/80 px-3 py-2 text-xs leading-snug text-white">
        {photo ? (
          <details>
            <summary className="cursor-pointer focus-visible:outline-2 focus-visible:outline-white">
              Photo: {venue.image_attribution} · {venue.image_license}
            </summary>
            <div className="mt-2 max-h-32 space-y-1 overflow-y-auto">
              <a href={venue.image_source_url!} target="_blank" rel="noopener noreferrer" className="block underline">
                {venue.image_title || venue.name} — Wikimedia Commons
              </a>
              <a href={venue.image_license_url!} target="_blank" rel="noopener noreferrer" className="block underline">
                {venue.image_license} licence
              </a>
              {venue.image_credit && <p>{venue.image_credit}</p>}
              <p>Preview cropped to fit. Open the source for the full image.</p>
            </div>
          </details>
        ) : <span>Category illustration · venue photo not available</span>}
      </div>
    </>
  )
}

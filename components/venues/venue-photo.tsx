"use client"

import Image from "next/image"
import { useEffect, useRef, useState } from "react"
import { googlePlaceId } from "@/lib/google-venue-photos.mjs"
import { categoryImage, categoryLabel, venuePhotoUrl, venueGooglePhotoEndpoint, type Venue } from "@/lib/venue-meta"

/** Credits travel with the photo in both cards and the surprise-pick view. */
export function VenuePhoto({ venue, sizes, className }: { venue: Venue; sizes: string; className?: string }) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null)
  const element = useRef<HTMLDivElement>(null)
  type GooglePhoto = { imageUrl: string; sourceUrl: string; authors: { name: string; uri: string | null; avatar: string | null }[] }
  const [resolved, setResolved] = useState<{ candidate: string; photo: GooglePhoto } | null>(null)
  const candidate = venueGooglePhotoEndpoint(venue) ?? venuePhotoUrl(venue)
  const isGoogle = Boolean(googlePlaceId(venue.image_url))
  const google = resolved?.candidate === candidate ? resolved.photo : null
  const photo = candidate && candidate !== failedUrl ? (isGoogle ? google?.imageUrl ?? null : candidate) : null
  useEffect(() => {
    if (!isGoogle || !candidate || !element.current) return
    const controller = new AbortController()
    let started = false
    const load = async () => {
      if (started) return
      started = true
      try {
        const response = await fetch(candidate, { signal: controller.signal, cache: 'no-store' })
        const result = await response.json()
        if (response.ok && result.photo && !controller.signal.aborted) setResolved({ candidate, photo: result.photo })
      } catch { /* Category artwork remains available when Google cannot load. */ }
    }
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) { observer.disconnect(); void load() }
    })
    observer.observe(element.current)
    return () => { observer.disconnect(); controller.abort() }
  }, [candidate, isGoogle])
  return (
    <div ref={element} className="absolute inset-0">
      <Image
        src={photo ?? categoryImage(venue.category)}
        alt={photo ? `Photo of ${venue.name}` : `${categoryLabel(venue.category)} illustration, not a photo of this venue`}
        fill
        quality={60}
        unoptimized={Boolean(photo)}
        sizes={sizes}
        className={className}
        onError={() => { if (candidate && photo) setFailedUrl(candidate) }}
      />
      <div className="absolute inset-x-0 bottom-0 z-10 bg-black/80 px-3 py-2 text-xs leading-snug text-white">
        {photo && isGoogle && google ? (
          <div className="space-y-1">
            <a href={google.sourceUrl} target="_blank" rel="noopener noreferrer" translate="no" className="block whitespace-nowrap font-normal not-italic underline">Google Maps</a>
            {google.authors.map((author, index) => (
              <span key={index} className="flex items-center gap-1.5">
                {author.avatar && <img src={author.avatar} alt="" className="size-5 rounded-full" />}
                {author.uri ? <a href={author.uri} target="_blank" rel="noopener noreferrer" className="underline">{author.name}</a> : author.name}
              </span>
            ))}
          </div>
        ) : photo ? (
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
    </div>
  )
}

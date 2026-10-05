"use client"

import { useEffect, useRef, useState } from "react"
import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react"
import { useLocation } from "@/components/location-provider"
import { useDirectoryPage } from "@/hooks/use-directory-page"
import { VenueCard } from "@/components/venues/venue-card"
import { milesBetween, type Venue } from "@/lib/venue-meta"
import { SectionHeader } from "./section-header"

export function LocalPlaces() {
  const { coords, label } = useLocation()
  const url = coords ? `/api/home/local-places?lat=${coords.lat}&lng=${coords.lng}` : "/api/home/local-places"
  const feed = useDirectoryPage<{ venues: Venue[] }>(url, !!coords)
  const venues = feed.pages[0]?.venues ?? []
  const rail = useRef<HTMLUListElement>(null)
  const [paused, setPaused] = useState(false)
  const [hovered, setHovered] = useState(false)
  const [focused, setFocused] = useState(false)
  const [visible, setVisible] = useState(false)
  const [reducedMotion, setReducedMotion] = useState(false)

  useEffect(() => {
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)")
    const update = () => setReducedMotion(motion.matches)
    update()
    motion.addEventListener("change", update)
    return () => motion.removeEventListener("change", update)
  }, [])

  useEffect(() => {
    const node = rail.current
    if (!node) return
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting))
    observer.observe(node)
    return () => observer.disconnect()
  }, [venues])

  useEffect(() => { if (rail.current) rail.current.scrollLeft = 0 }, [url])

  useEffect(() => {
    const node = rail.current
    if (!node || paused || hovered || focused || reducedMotion || !visible || venues.length < 2) return
    let frame = 0
    let last = 0
    let position = node.scrollLeft
    const tick = (now: number) => {
      if (last && document.visibilityState === "visible") {
        position += Math.min(now - last, 80) * 0.018
        const end = node.scrollWidth - node.clientWidth
        if (end > 0 && position >= end) position = 0
        node.scrollLeft = position
      }
      last = now
      frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [venues, paused, hovered, focused, reducedMotion, visible])

  function move(direction: number) {
    setPaused(true)
    const node = rail.current
    if (node) node.scrollBy({ left: direction * (node.firstElementChild?.clientWidth ?? 280), behavior: reducedMotion ? "instant" : "smooth" })
  }

  return (
    <section aria-labelledby="local-places-title" className="flex min-w-0 flex-col gap-4">
      <SectionHeader id="local-places-title" title="Local Places" href="/venues" linkLabel="View all places" />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-lg text-sm leading-relaxed text-muted-foreground">Closest places in each category, then the next closest{coords ? ` · near ${label}` : ""}.</p>
        {venues.length > 0 && <div className="flex items-center gap-2">
          <button type="button" aria-label="Previous local places" onClick={() => move(-1)} className="flex size-10 items-center justify-center rounded-full border bg-card hover:bg-muted"><ChevronLeft className="size-4" aria-hidden /></button>
          {!reducedMotion && <button type="button" aria-label={paused ? "Play local places reel" : "Pause local places reel"} aria-pressed={paused} onClick={() => setPaused((value) => !value)} className="inline-flex min-h-10 items-center gap-2 rounded-full border bg-card px-3 text-sm font-semibold hover:bg-muted">
            {paused ? <Play className="size-4" aria-hidden /> : <Pause className="size-4" aria-hidden />}{paused ? "Play" : "Pause"}
          </button>}
          <button type="button" aria-label="Next local places" onClick={() => move(1)} className="flex size-10 items-center justify-center rounded-full border bg-card hover:bg-muted"><ChevronRight className="size-4" aria-hidden /></button>
        </div>}
      </div>
      {!coords ? <p role="status" className="text-sm text-muted-foreground">Choose a location to see places near you.</p>
        : feed.loading ? <p role="status" className="rounded-xl border bg-card p-6 text-muted-foreground">Finding local places…</p>
        : feed.error ? <p role="alert" className="rounded-xl border bg-card p-6">{feed.error} <button type="button" onClick={feed.retry} className="font-semibold underline">Retry</button></p>
        : !venues.length ? <p className="rounded-xl border border-dashed bg-card p-6 text-muted-foreground">No local places found yet. Try another location.</p>
        : <ul ref={rail} aria-label="Local places, nearest in each category first" tabIndex={0}
            onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}
            onFocusCapture={() => setFocused(true)} onBlurCapture={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setFocused(false) }}
            onPointerDown={() => setPaused(true)} onWheel={() => setPaused(true)}
            onKeyDown={(event) => { if (event.target === event.currentTarget && (event.key === "ArrowLeft" || event.key === "ArrowRight")) { event.preventDefault(); move(event.key === "ArrowRight" ? 1 : -1) } }}
            className="flex gap-4 overflow-x-auto overscroll-x-contain rounded-xl pb-4">
            {venues.map((venue) => <li key={venue.id} data-category={venue.category} className="w-[min(80vw,300px)] shrink-0">
              <VenueCard venue={venue} distance={coords && venue.latitude != null && venue.longitude != null ? milesBetween(coords, {lat: venue.latitude, lng: venue.longitude}) : null} />
            </li>)}
          </ul>}
    </section>
  )
}

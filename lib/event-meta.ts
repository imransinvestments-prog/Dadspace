import type { DadEvent } from "./types"

export type EventCategory = "seasonal" | "swim" | "stage" | "active" | "outdoor" | "crafts" | "story" | "music" | "family"

type CategoryDef = { key: EventCategory; label: string; pattern: RegExp; images: string[] }

// Prefer specific intent words. Broad words such as "show", "play" and a venue
// containing "park" are deliberately avoided because they caused false matches.
const CATEGORIES: CategoryDef[] = [
  {
    key: "seasonal",
    label: "Seasonal",
    pattern: /hallowe?en|pumpkin|spooky|christmas|santa|grotto|festive|fireworks|bonfire|easter|diwali|panto/,
    images: ["/images/events/seasonal.png"],
  },
  {
    key: "stage",
    label: "Film & theatre",
    pattern: /\bfilm\b|cinema|cinemagic|screening|\bmovie\b|theatre|theater|musical|puppet|circus|comedy|performance/,
    images: ["/images/events/stage.png"],
  },
  {
    key: "swim",
    label: "Swimming",
    pattern: /\bswimming\b|swim session|swim lesson|water babies|aqua (?:class|session)|pool session|learn to swim/,
    images: ["/images/events/swim.png"],
  },
  {
    key: "active",
    label: "Sport & active",
    pattern: /gymnast|tumble|rugby|football|sport|parkrun|\brun\b|tennis|climb|skate|cycl|bike|martial|karate|judo|trampolin|multi-skill|athletic|cricket|netball/,
    images: ["/images/events/active-play.png", "/images/event-sport.png"],
  },
  {
    key: "outdoor",
    label: "Outdoors & nature",
    pattern: /forest school|nature|wildlife|bat walk|guided walk|woodland|\bfarm\b|beach|nature trail|garden trail|country park activity|bird|bug hunt|pond dipping/,
    images: ["/images/event-outdoor.png"],
  },
  {
    key: "crafts",
    label: "Arts & crafts",
    pattern: /craft|\bart\b|arts|paint|lego|draw|messy|creative workshop|clay|pottery|sewing|model making/,
    images: ["/images/event-crafts.png"],
  },
  {
    key: "story",
    label: "Stories & learning",
    pattern: /story|stories|book|library|read|phonics|homework|science|museum activity|history workshop|stem|coding|learning session|exhibit/,
    images: ["/images/event-story.png"],
  },
  {
    key: "music",
    label: "Music & dance",
    pattern: /music|sing|rhyme|danc|disco|ballet|\bband\b|choir|concert/,
    images: ["/images/events/music.png"],
  },
]

const FAMILY: CategoryDef = { key: "family", label: "Family days out", pattern: /./, images: ["/images/events/family-day.png"] }

export const EVENT_CATEGORIES: { key: EventCategory; label: string }[] = [...CATEGORIES, FAMILY].map(({ key, label }) => ({ key, label }))

function definitionFor(event: Pick<DadEvent, "title" | "description" | "location">): CategoryDef {
  const title = event.title.toLowerCase()
  const description = (event.description ?? "").toLowerCase()

  // Title is the strongest signal. Only fall back to description when the title
  // is genuinely unclear; location alone never decides a category.
  const titleMatch = CATEGORIES.find((c) => c.pattern.test(title))
  if (titleMatch) return titleMatch
  const descriptionMatch = CATEGORIES.find((c) => c.pattern.test(description))
  if (descriptionMatch) return descriptionMatch
  return FAMILY
}

export function eventCategory(event: Pick<DadEvent, "title" | "description" | "location">): EventCategory {
  return definitionFor(event).key
}

export function categoryLabel(key: EventCategory): string {
  return EVENT_CATEGORIES.find((c) => c.key === key)?.label ?? "Family days out"
}

function hash(value: string) {
  let h = 0
  for (let i = 0; i < value.length; i++) h = (h * 31 + value.charCodeAt(i)) | 0
  return Math.abs(h)
}

/** The event's own image from the database when there is one, otherwise a stock image for its category. */
export function eventImage(event: DadEvent): { src: string; isOwn: boolean } {
  if (event.image_url) return { src: event.image_url, isOwn: true }
  const { images } = definitionFor(event)
  return { src: images[hash(event.id) % images.length], isOwn: false }
}

export function isFreeEvent(cost: string | null): boolean {
  return !!cost && /\bfree\b/i.test(cost) && !/£\s*\d/.test(cost)
}

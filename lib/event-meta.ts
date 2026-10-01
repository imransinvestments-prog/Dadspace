import type { DadEvent } from "./types"

export type EventCategory = "holiday_camps" | "seasonal" | "swim" | "stage" | "active" | "outdoor" | "crafts" | "story" | "music" | "family"

type CategoryDef = { key: EventCategory; label: string; pattern: RegExp; images: string[] }

const HOLIDAY_CAMPS: CategoryDef = {
  key: "holiday_camps",
  label: "Holiday camps",
  pattern: /holiday camp|half[- ]?term camp|summer camp|easter camp|christmas camp|school holiday camp|multi[- ]?activity camp|football camp|sports camp|dance camp|drama camp|performing arts camp/,
  images: ["/images/events/active-play.png", "/images/events/family-day.png"],
}

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
const ALL_DEFS = [HOLIDAY_CAMPS, ...CATEGORIES, FAMILY]

export const EVENT_CATEGORIES: { key: EventCategory; label: string }[] = ALL_DEFS.map(({ key, label }) => ({ key, label }))

const STORED_CATEGORY_MAP: Record<string, EventCategory> = {
  holiday_camps: "holiday_camps",
  sports: "active",
  swimming: "swim",
  outdoors_nature: "outdoor",
  film_theatre: "stage",
  arts_crafts: "crafts",
  museums_heritage: "story",
  farms_animals: "outdoor",
  libraries: "story",
  baby_toddler: "family",
  family_days_out: "family",
  other: "family",
}

function definitionFor(event: Pick<DadEvent, "title" | "description" | "location" | "category" | "is_holiday_camp">): CategoryDef {
  if (event.is_holiday_camp) return HOLIDAY_CAMPS
  const stored = event.category ? STORED_CATEGORY_MAP[event.category] : undefined
  if (stored) return ALL_DEFS.find((c) => c.key === stored) ?? FAMILY

  const title = event.title.toLowerCase()
  const description = (event.description ?? "").toLowerCase()
  const holidayMatch = HOLIDAY_CAMPS.pattern.test(`${title} ${description}`)
  if (holidayMatch) return HOLIDAY_CAMPS

  // Legacy rows without an extracted category still use the safer heuristic.
  const titleMatch = CATEGORIES.find((c) => c.pattern.test(title))
  if (titleMatch) return titleMatch
  const descriptionMatch = CATEGORIES.find((c) => c.pattern.test(description))
  if (descriptionMatch) return descriptionMatch
  return FAMILY
}

export function eventCategory(event: Pick<DadEvent, "title" | "description" | "location" | "category" | "is_holiday_camp">): EventCategory {
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

export function eventImage(event: DadEvent): { src: string; isOwn: boolean } {
  if (event.image_url) return { src: event.image_url, isOwn: true }
  const { images } = definitionFor(event)
  return { src: images[hash(event.id) % images.length], isOwn: false }
}

export function isFreeEvent(cost: string | null): boolean {
  return !!cost && /\bfree\b/i.test(cost) && !/£\s*\d/.test(cost)
}

import type { DadEvent } from "./types"

export type EventCategory = "seasonal" | "swim" | "stage" | "active" | "outdoor" | "crafts" | "story" | "music" | "family"

type CategoryDef = { key: EventCategory; label: string; pattern: RegExp; images: string[] }

// Order matters: the first match wins, so specific themes sit above broad ones.
const CATEGORIES: CategoryDef[] = [
  {
    key: "seasonal",
    label: "Seasonal",
    pattern: /hallowe?en|pumpkin|spooky|christmas|santa|grotto|festive|fireworks|bonfire|easter|diwali|panto/,
    images: ["/images/events/seasonal.png"],
  },
  {
    key: "swim",
    label: "Swimming",
    pattern: /swim|water babies|splash|aqua|\bpool\b/,
    images: ["/images/events/swim.png"],
  },
  {
    key: "stage",
    label: "Film & theatre",
    pattern: /film|cinema|cinemagic|screening|movie|theatre|theater|musical|puppet|circus|comedy|\bshow\b|\bplay\b.*\bstage\b/,
    images: ["/images/events/stage.png"],
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
    pattern: /forest school|nature|wildlife|bat walk|\bwalk\b|woodland|\bfarm\b|beach|\btrail|garden|country park|bird|bug hunt|pond/,
    images: ["/images/event-outdoor.png"],
  },
  {
    key: "crafts",
    label: "Arts & crafts",
    pattern: /craft|\bart\b|arts|paint|lego|draw|messy|workshop|clay|pottery|sewing|build/,
    images: ["/images/event-crafts.png"],
  },
  {
    key: "story",
    label: "Stories & learning",
    pattern: /story|stories|book|library|read|phonics|homework|science|museum|history|stem|coding|learn|exhibit|club/,
    images: ["/images/event-story.png"],
  },
  {
    key: "music",
    label: "Music & dance",
    pattern: /music|sing|rhyme|danc|disco|ballet|\bband\b|choir|bounce|concert/,
    images: ["/images/events/music.png"],
  },
]

const FAMILY: CategoryDef = { key: "family", label: "Family days out", pattern: /./, images: ["/images/events/family-day.png"] }
const LOOSE_OUTDOOR = /\bpark\b|outdoor|field|meadow/

export const EVENT_CATEGORIES: { key: EventCategory; label: string }[] = [...CATEGORIES, FAMILY].map(({ key, label }) => ({ key, label }))

function definitionFor(event: Pick<DadEvent, "title" | "description" | "location">): CategoryDef {
  const title = event.title.toLowerCase()
  const withDescription = `${title} ${event.description ?? ""}`.toLowerCase()
  for (const text of [title, withDescription]) {
    const match = CATEGORIES.find((c) => c.pattern.test(text))
    if (match) return match
  }
  if (LOOSE_OUTDOOR.test(`${withDescription} ${event.location ?? ""}`.toLowerCase())) {
    return CATEGORIES.find((c) => c.key === "outdoor")!
  }
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

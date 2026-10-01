import type { DadEvent } from "./types"

export function slugifyEventTitle(title: string): string {
  return title
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "family-event"
}

export function eventSlug(event: Pick<DadEvent, "id" | "title">): string {
  return `${slugifyEventTitle(event.title)}--${event.id}`
}

export function eventIdFromSlug(slug: string): string {
  const marker = slug.lastIndexOf("--")
  return marker >= 0 ? slug.slice(marker + 2) : slug
}

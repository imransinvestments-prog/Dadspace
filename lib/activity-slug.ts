import type { DadActivity } from "./types"

export function slugifyActivityTitle(title: string): string {
  return title
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "family-activity"
}

export function activitySlug(activity: Pick<DadActivity, "id" | "title">): string {
  return `${slugifyActivityTitle(activity.title)}--${activity.id}`
}

export function activityIdFromSlug(slug: string): string {
  const marker = slug.lastIndexOf("--")
  return marker >= 0 ? slug.slice(marker + 2) : slug
}

import type { DadActivity } from "./types"

export function originalActivityDescription(activity: DadActivity): string {
  const place = activity.venue_name || activity.location
  const parts = [
    place ? `${activity.title} is a regular family activity at ${place}.` : `${activity.title} is a regular family activity.`,
    activity.schedule_text ? `Schedule: ${activity.schedule_text}.` : null,
    activity.age_range ? `Age guidance: ${activity.age_range}.` : null,
    activity.cost_text ? `Price: ${activity.cost_text}.` : "Check the organiser's site for current pricing.",
  ].filter(Boolean)
  return parts.join(" ")
}

import type { DadActivity } from "./types"

export function originalActivityDescription(activity: DadActivity): string {
  const place = activity.venue_name || activity.location
  const parts = [
    place ? `${activity.title} is a regular family activity at ${place}.` : `${activity.title} is a regular family activity.`,
    activity.schedule_text ? `Schedule: ${activity.schedule_text}.` : null,
    activity.age_range ? `Age guidance: ${activity.age_range}.` : null,
    activity.cost_text ? `Price: ${activity.cost_text}.` : "Check the organiser's site for current pricing.",
  ].filter(Boolean)
  // Keep our own summary while retaining explicit attendance facts from the
  // source evidence. Unrecognised wording remains for source review.
  const evidence = (activity.description ?? "").replace(/\s+/g, " ")
  if (/services are restricted to those living in the London Borough of Sutton only/i.test(evidence)) {
    parts.push("For London Borough of Sutton residents only.")
  }
  if (/book a ticket for each child and adult/i.test(evidence)) {
    parts.push("Book a ticket for each child and adult attending.")
  } else if (/only book a ticket for the child|book a ticket for each child attending/i.test(evidence)
    && /adults (?:do not|don't) (?:need|require) (?:a )?ticket/i.test(evidence)) {
    parts.push("Book tickets for children; adults do not need a ticket.")
  }
  if (/no booking necessary.*first come first served/i.test(evidence)) {
    parts.push("No advance booking; places are first come, first served.")
  }
  if (/children must be accompanied by a responsible adult/i.test(evidence)) {
    parts.push("Children must be accompanied by a responsible adult.")
  }
  if (/log in with your library credentials to reserve your place/i.test(evidence)) {
    parts.push("Library-card booking is available.")
  }
  return parts.join(" ")
}


import { formatEventDate } from "./dates"
import { categoryLabel, eventCategory, isFreeEvent } from "./event-meta"
import type { DadEvent } from "./types"

export function originalEventDescription(event: DadEvent): string {
  const category = categoryLabel(eventCategory(event)).toLowerCase()
  const date = formatEventDate(event.start_date, event.end_date)
  const place = event.location ? ` at ${event.location}` : ""
  const ages = event.age_range ? ` It is listed for ages ${event.age_range}.` : ""
  const price = event.cost_text
    ? isFreeEvent(event.cost_text)
      ? " It is listed as free."
      : ` The listed price is ${event.cost_text}.`
    : " Check the organiser's site for the latest price."

  return `${event.title} is a ${category} option${place} on ${date}.${ages}${price} Check the official listing before travelling for current times, availability and booking details.`
}

import { eventImage, isFreeEvent } from "@/lib/event-meta"
import { siteName, siteUrl } from "@/lib/seo"
import type { DadEvent } from "@/lib/types"

const MAX_ITEMS = 100

function absolute(src: string) {
  return src.startsWith("http") ? src : `${siteUrl}${src}`
}

function eventSchema(event: DadEvent) {
  const url = event.event_url || event.source_url || undefined
  const free = isFreeEvent(event.cost_text)
  const price = event.cost_text?.match(/£\s*(\d+(?:\.\d{1,2})?)/)?.[1]

  return {
    "@type": "Event",
    name: event.title,
    description: event.description?.slice(0, 500) || undefined,
    startDate: event.start_date.slice(0, 10),
    endDate: (event.end_date ?? event.start_date).slice(0, 10),
    eventStatus: "https://schema.org/EventScheduled",
    eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
    image: [absolute(eventImage(event).src)],
    url,
    isAccessibleForFree: free || undefined,
    typicalAgeRange: event.age_range || undefined,
    location: event.location
      ? { "@type": "Place", name: event.location, address: { "@type": "PostalAddress", streetAddress: event.location, addressCountry: "GB" } }
      : undefined,
    offers:
      free || price
        ? { "@type": "Offer", price: free ? "0" : price, priceCurrency: "GBP", availability: "https://schema.org/InStock", url }
        : undefined,
  }
}

export function EventsJsonLd({ events }: { events: DadEvent[] }) {
  const data = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "CollectionPage",
        "@id": `${siteUrl}/events#page`,
        url: `${siteUrl}/events`,
        name: "Family events and things to do with kids across the UK",
        isPartOf: { "@type": "WebSite", name: siteName, url: siteUrl },
        inLanguage: "en-GB",
        mainEntity: { "@id": `${siteUrl}/events#list` },
      },
      {
        "@type": "ItemList",
        "@id": `${siteUrl}/events#list`,
        numberOfItems: Math.min(events.length, MAX_ITEMS),
        itemListElement: events.slice(0, MAX_ITEMS).map((event, i) => ({
          "@type": "ListItem",
          position: i + 1,
          item: eventSchema(event),
        })),
      },
    ],
  }

  return (
    <script
      type="application/ld+json"
      // JSON.stringify output with "<" escaped cannot break out of the script tag.
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  )
}

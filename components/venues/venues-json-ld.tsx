import { JsonLd, absoluteUrl } from "@/components/seo/json-ld"
import { siteUrl } from "@/lib/seo"
import { categoryLabel, venueImage, type Venue } from "@/lib/venue-meta"

const MAX_ITEMS = 100

const SCHEMA_TYPES: Record<string, string> = {
  museum: "Museum",
  park: "Park",
  playground: "Playground",
  library: "Library",
  cafe: "CafeOrCoffeeShop",
  leisure: "SportsActivityLocation",
  soft_play: "EntertainmentBusiness",
  zoo: "Zoo",
  aquarium: "Aquarium",
}

function venueSchema(venue: Venue) {
  return {
    "@type": (venue.category && SCHEMA_TYPES[venue.category]) || "TouristAttraction",
    name: venue.name,
    description: venue.description || `${categoryLabel(venue.category)}${venue.town ? ` in ${venue.town}` : ""}, family-friendly.`,
    image: absoluteUrl(venueImage(venue)),
    url: venue.website_url || undefined,
    telephone: venue.phone || undefined,
    address: {
      "@type": "PostalAddress",
      streetAddress: venue.address || undefined,
      addressLocality: venue.town || undefined,
      postalCode: venue.postcode || undefined,
      addressRegion: venue.region || undefined,
      addressCountry: "GB",
    },
    geo:
      venue.latitude != null && venue.longitude != null
        ? { "@type": "GeoCoordinates", latitude: venue.latitude, longitude: venue.longitude }
        : undefined,
    isAccessibleForFree: venue.is_free ?? undefined,
    publicAccess: true,
    amenityFeature: venue.facilities.length
      ? venue.facilities.map((f) => ({ "@type": "LocationFeatureSpecification", name: f.replace(/_/g, " "), value: true }))
      : undefined,
  }
}

export function VenuesJsonLd({ venues }: { venues: Venue[] }) {
  const listed = venues.slice(0, MAX_ITEMS)

  return (
    <JsonLd
      data={{
        "@context": "https://schema.org",
        "@graph": [
          {
            "@type": "CollectionPage",
            "@id": `${siteUrl}/venues#page`,
            url: `${siteUrl}/venues`,
            name: "Family-friendly venues across the UK",
            description: "Soft play, parks, museums, libraries and more across the UK, with facilities, prices and opening times for dads and families.",
            inLanguage: "en-GB",
            isPartOf: { "@id": `${siteUrl}/#website` },
            mainEntity: { "@id": `${siteUrl}/venues#list` },
          },
          {
            "@type": "ItemList",
            "@id": `${siteUrl}/venues#list`,
            numberOfItems: listed.length,
            itemListElement: listed.map((venue, i) => ({ "@type": "ListItem", position: i + 1, item: venueSchema(venue) })),
          },
        ],
      }}
    />
  )
}

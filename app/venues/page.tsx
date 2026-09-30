import { VenuesDirectory } from "@/components/venues/venues-directory"
import { fetchVenues } from "@/lib/venues"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "Family-Friendly Venues",
  "/venues",
  "Family-friendly venues near you: soft play, parks, museums and more, with facilities and opening times.",
)

export const revalidate = 600

export default async function VenuesPage() {
  const { venues, isPreview } = await fetchVenues()
  return <VenuesDirectory venues={venues} isPreview={isPreview} />
}

import { VenuesDirectory } from "@/components/venues/venues-directory"
import { VenuesJsonLd } from "@/components/venues/venues-json-ld"
import { fetchVenues } from "@/lib/venues"
import { pageMetadata } from "@/lib/seo"
import { getSupabase } from '@/lib/supabase'

export const metadata = pageMetadata(
  "Family-Friendly Venues",
  "/venues",
  "Family-friendly venues near you: soft play, parks, museums and more, with facilities and opening times.",
)

export const revalidate = 600

export default async function VenuesPage() {
  const { venues, isPreview } = await fetchVenues()
  const db=getSupabase()
  const {data:categories}=db?await db.rpc('venue_category_counts'):{data:null}
  return (
    <>
      {venues.length ? <VenuesJsonLd venues={venues} /> : null}
      <VenuesDirectory venues={venues} isPreview={isPreview} allCategories={categories??[]} />
    </>
  )
}

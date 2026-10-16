import type { Venue } from "@/lib/venue-meta"

// Access is independent of price, opening hours and child suitability. Imported
// tags describe the source's evidence; they are not an independent verification.
export function accessDescription(access: string | null | undefined) {
  switch (access?.trim().toLowerCase()) {
    case "yes": case "public": return "Public access indicated. Check opening times and entry requirements before visiting."
    case "customers": return "Customer access only. Check entry requirements and any charges before visiting."
    case "permissive": return "Access by the owner's permission; conditions may change. Check before visiting."
    case "residents": return "Residents only. Check that you are eligible before visiting."
    case "permit": return "Permit required. Check eligibility and obtain permission before visiting."
    case "private": return "Private access. Not open for general public visits."
    case "no": case "closed": return "No public access indicated."
    case "school": case "students": return "School or student access only. Check eligibility before visiting."
    case "visitors": return "Visitor access conditions apply. Check entry requirements before visiting."
    case "restricted": case "official": case "destination": case "passengers": case "children":
      return "Restricted access indicated. Confirm eligibility and conditions before visiting."
    default: return "Access information not supplied. Check with the venue before visiting."
  }
}

export function VenueAccess({ venue }: { venue: Venue }) {
  return <p className="rounded-lg border bg-muted/50 p-3 text-sm leading-relaxed" aria-label="Access information">{accessDescription(venue.access)}</p>
}

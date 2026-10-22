export const VENUE_CHECK_LABELS={identity:"Correct venue identity?",location:"Correct address and position?",source:"Usable primary evidence for this venue?",access:"Visitor restrictions checked?",visitor_facts:"Hours and entry facts checked, with unknowns explicit?",photo_rights:"Image attribution and reuse rights checked?"} as const
export type VenueChecks=Record<keyof typeof VENUE_CHECK_LABELS,string>
export function validVenueChecks(value: unknown): value is VenueChecks {
 if(!value || typeof value!=="object" || Array.isArray(value))return false
 const row=value as Record<string,unknown>
 return Object.keys(row).length===Object.keys(VENUE_CHECK_LABELS).length && Object.keys(VENUE_CHECK_LABELS).every(k=>["yes","no","unknown"].includes(String(row[k])))
}

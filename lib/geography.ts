export type GeographicArea = { code: string; name: string; kind: string }
export type GeographyScenario = { id: string; postcode: string; label: string; tag: string; state: string;
  expected_nation: string; expected_region?: string | null; expected_council?: string;
  expected_council_code?: string; latitude?: number; longitude?: number; radius_km: number; reason?: string }
export type CoverageObservation = { case_id: string; feature: string; status: string; count: number | null;
  completeness: string; reported_total?: number | null; http_status?: number | null; request_path?: string }

/** Platform-independent manifest serialization; line endings never change identity. */
export function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) return "[" + value.map(canonicalJson).join(",") + "]"
  if (value !== null && typeof value === "object") return "{" + Object.keys(value).sort().map(key => JSON.stringify(key) + ":" + canonicalJson((value as Record<string, unknown>)[key])).join(",") + "}"
  return JSON.stringify(value)
}

export function referenceSummary(areas: GeographicArea[], cases: GeographyScenario[]) {
  const councils = areas.filter(area => area.kind === "council")
  const sampled = new Set(cases.filter(row => row.state === "reference_verified").map(row => row.expected_council_code))
  return { councils: councils.length, sampledCouncils: councils.filter(area => sampled.has(area.code)).length,
    untestedCouncils: councils.filter(area => !sampled.has(area.code)).length,
    verifiedPostcodes: cases.filter(row => row.state === "reference_verified").length,
    blockedPostcodes: cases.filter(row => row.state === "blocked_licence").length }
}

export function baselineCompatible(release: string, expectedPackHash: string, report: { reference_release: string; test_pack_sha256: string }) {
  return report.reference_release === release && report.test_pack_sha256 === expectedPackHash
}

export function observationLabel(row?: CoverageObservation) {
  if (!row) return "Untested"
  if (row.status === "blocked_licence") return "Licence blocked"
  if (row.status === "unavailable") return "Unavailable"
  if (row.status === "failed") return "Failed validation"
  if (row.status === "passed") return "Lookup passed"
  if (row.status === "observed_empty") return row.completeness === "not_established" ? "0 visible · completeness unknown" : "0 returned"
  if (row.status === "observed_nonempty") return `${row.count} returned${row.completeness === "first_page" ? " · first page" : row.completeness === "not_established" ? " · completeness unknown" : ""}`
  return "Untested"
}

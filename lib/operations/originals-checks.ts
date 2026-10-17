export const ORIGINALS_CHECKS = [
  { key: "originality", label: "Originality", help: "Does this feel distinct, without obvious copying or repetition?" },
  { key: "claims", label: "Claims", help: "Are factual claims supported or appropriately qualified, with no misleading promises?" },
  { key: "tone", label: "Tone", help: "Is the writing clear, welcoming, practical and appropriate for Dadspace families?" },
  { key: "length", label: "Length", help: "Is the amount of detail appropriate for a daily tip or weekly guide?" },
] as const
export type OriginalsChecks = Record<(typeof ORIGINALS_CHECKS)[number]["key"], string>
export function validOriginalsChecks(value: unknown): value is OriginalsChecks {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false
  const record = value as Record<string, unknown>
  return ORIGINALS_CHECKS.every(({ key }) => ["yes", "no", "unknown"].includes(String(record[key])))
}
export function originalBodyWords(fields: Record<string, unknown>) {
  if (!Array.isArray(fields.sections)) return null
  const text = fields.sections.flatMap(section => {
    if (!section || typeof section !== "object") return []
    return [section.heading, ...(Array.isArray(section.paragraphs) ? section.paragraphs : [])].filter(value => typeof value === "string")
  }).join(" ").trim()
  return text ? text.split(/\s+/).length : 0
}
export function previousOriginalsChecks(comments: Array<{ id: number; body: string; user: { login: string } }>, rowId: string, fingerprint: string): OriginalsChecks | undefined {
  // Do not infer individual checks from a generic approval or another version.
  for (const comment of [...comments].sort((a, b) => b.id - a.id)) {
    if (comment.user.login.toLowerCase() !== "imransinvestments-prog" || !comment.body.startsWith("Dadspace owner review v1\n")) continue
    if (comment.body.match(/^Reviewed record: (.+)$/m)?.[1] !== rowId || comment.body.match(/^Snapshot SHA-256: (.+)$/m)?.[1] !== fingerprint) continue
    try {
      const checks = JSON.parse(comment.body.match(/^Originals editorial checks: (\{[^\n]+\})$/m)?.[1] || "null")
      return validOriginalsChecks(checks) ? checks : undefined
    } catch { return undefined }
  }
}

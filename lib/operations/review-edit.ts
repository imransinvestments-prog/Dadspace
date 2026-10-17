import "server-only"

export const EDIT_FIELDS = ["venue_name", "category", "address", "postcode", "latitude", "longitude", "website", "access"] as const
export type EditField = typeof EDIT_FIELDS[number]
export type EditPatch = { changes: Partial<Record<EditField, string | number | null>>; source_url: string }
const limits = { venue_name: 200, category: 100, address: 500, postcode: 20, website: 2048, access: 100 }
export function publicEvidenceUrl(value: unknown): value is string {
  if (typeof value !== "string" || value.length > 2048 || /[\s\\]/.test(value)) return false
  try { const u = new URL(value); return u.protocol === "https:" && !!u.hostname && !u.username && !u.password && (!u.port || u.port === "443") }
  catch { return false }
}
export function editPatch(value: unknown): EditPatch | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null
  const input = value as Record<string, unknown>
  if (Object.keys(input).some(k => !["changes", "source_url"].includes(k)) || !publicEvidenceUrl(input.source_url) ||
      !input.changes || typeof input.changes !== "object" || Array.isArray(input.changes)) return null
  const fields = input.changes as Record<string, unknown>, keys = Object.keys(fields)
  if (!keys.length || keys.some(k => !EDIT_FIELDS.includes(k as EditField))) return null
  const changes: EditPatch["changes"] = {}
  for (const key of keys) {
    const name = key as EditField, v = fields[key]
    if (name === "latitude" || name === "longitude") {
      const max = name === "latitude" ? 90 : 180
      if (v !== null && (typeof v !== "number" || !Number.isFinite(v) || Math.abs(v) > max)) return null
      changes[name] = v as number | null
    } else {
      if (v !== null && typeof v !== "string") return null
      const text = typeof v === "string" ? v.trim() || null : null
      if ((name === "venue_name" || name === "category") && !text) return null
      if (text && (text.length > limits[name] || /[\u0000-\u001f\u007f]/.test(text))) return null
      if (name === "website" && text && !publicEvidenceUrl(text)) return null
      changes[name] = text
    }
  }
  const has = (key: EditField) => Object.hasOwn(changes, key)
  if (has("latitude") !== has("longitude") || (has("latitude") && ((changes.latitude === null) !== (changes.longitude === null)))) return null
  // A location correction must explicitly replace or clear the old coordinate pair.
  if ((has("address") || has("postcode")) && !has("latitude")) return null
  return { changes, source_url: input.source_url }
}
export function editForm(form: FormData): EditPatch | null {
  const changes: Record<string, unknown> = {}
  for (const key of EDIT_FIELDS) if (form.get("edit_" + key) === "yes") {
    const raw = form.get(key)
    changes[key] = key === "latitude" || key === "longitude" ? raw === "" ? null : typeof raw === "string" ? Number(raw) : NaN : raw
  }
  return editPatch({ changes, source_url: form.get("evidence_url") })
}

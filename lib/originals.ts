import "server-only"
import { getSupabase } from "@/lib/supabase"

export type OriginalPost = {
  slug: string; cadence: "daily" | "weekly"; title: string; summary: string;
  published_at: string; sections: Array<{ heading: string; paragraphs: string[] }>;
}
const columns = "slug,cadence,title,summary,published_at,sections"
export async function getOriginals(cadence?: "daily" | "weekly") {
  const db = getSupabase()
  if (!db) throw new Error("Original content is unavailable")
  let query = db.from("original_posts").select(columns).lte("published_at", new Date().toISOString()).order("published_at", { ascending: false }).limit(60)
  if (cadence) query = query.eq("cadence", cadence)
  const { data, error } = await query
  if (error) throw new Error("Original content is unavailable")
  return (data ?? []) as OriginalPost[]
}
export async function getOriginal(slug: string) {
  const db = getSupabase()
  if (!db) throw new Error("Original content is unavailable")
  const { data, error } = await db.from("original_posts").select(columns).eq("slug", slug).lte("published_at", new Date().toISOString()).maybeSingle()
  if (error) throw new Error("Original content is unavailable")
  return data as OriginalPost | null
}
export function originalDate(value: string) {
  return new Date(value).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "Europe/London" })
}

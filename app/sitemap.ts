import type { MetadataRoute } from "next"
import { eventSlug } from "@/lib/event-slug"
import { getSupabase } from "@/lib/supabase"
import { siteUrl } from "@/lib/seo"

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date()
  const pages: Array<{
    path: string
    changeFrequency: "daily" | "weekly"
    priority: number
  }> = [
    { path: "", changeFrequency: "daily", priority: 1 },
    { path: "/news", changeFrequency: "daily", priority: 0.9 },
    { path: "/events", changeFrequency: "daily", priority: 0.9 },
    { path: "/deals", changeFrequency: "daily", priority: 0.9 },
    { path: "/venues", changeFrequency: "weekly", priority: 0.8 },
  ]

  const staticPages: MetadataRoute.Sitemap = pages.map(({ path, changeFrequency, priority }) => ({
    url: `${siteUrl}${path}`,
    lastModified: now,
    changeFrequency,
    priority,
  }))

  const db = getSupabase()
  if (!db) return staticPages

  const { data, error } = await db
    .from("collected_events")
    .select("id,title,last_verified_at")
    .order("last_verified_at", { ascending: false })
    .limit(1000)

  if (error || !data?.length) return staticPages

  const eventPages: MetadataRoute.Sitemap = data.map((row) => ({
    url: `${siteUrl}/events/${eventSlug({ id: String(row.id), title: String(row.title ?? "Family event") })}`,
    lastModified: row.last_verified_at ? new Date(String(row.last_verified_at)) : now,
    changeFrequency: "weekly" as const,
    priority: 0.7,
  }))

  return [...staticPages, ...eventPages]
}

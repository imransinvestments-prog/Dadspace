import type { MetadataRoute } from "next"
import { activitySlug } from "@/lib/activity-slug"
import { eventSlug } from "@/lib/event-slug"
import { getSupabase } from "@/lib/supabase"
import { siteUrl } from "@/lib/seo"
import { COMING_SOON } from "@/lib/launch"

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  if (COMING_SOON) return [{ url: siteUrl, changeFrequency: "weekly", priority: 1 }]
  const pages: Array<{
    path: string
    changeFrequency: "daily" | "weekly"
    priority: number
  }> = [
    { path: "", changeFrequency: "daily", priority: 1 },
    { path: "/news", changeFrequency: "daily", priority: 0.9 },
    { path: "/events", changeFrequency: "daily", priority: 0.9 },
    { path: "/activities", changeFrequency: "daily", priority: 0.9 },
    { path: "/deals", changeFrequency: "daily", priority: 0.9 },
    { path: "/venues", changeFrequency: "weekly", priority: 0.8 },
  ]

  const staticPages: MetadataRoute.Sitemap = pages.map(({ path, changeFrequency, priority }) => ({
    url: `${siteUrl}${path}`,
    changeFrequency,
    priority,
  }))

  const db = getSupabase()
  if (!db) return staticPages

  const [eventsResult, activitiesResult] = await Promise.all([
    db
      .from("collected_events")
      .select("id,title,last_verified_at")
      .eq("listing_type", "event")
      .order("last_verified_at", { ascending: false })
      .limit(1000),
    db
      .from("current_activities")
      .select("id,title,last_seen_at")
      .order("last_seen_at", { ascending: false })
      .limit(1000),
  ])

  const eventPages: MetadataRoute.Sitemap = eventsResult.error
    ? []
    : (eventsResult.data ?? []).map((row) => ({
        url: `${siteUrl}/events/${eventSlug({ id: String(row.id), title: String(row.title ?? "Family event") })}`,
        lastModified: row.last_verified_at ? new Date(String(row.last_verified_at)) : undefined,
        changeFrequency: "weekly" as const,
        priority: 0.7,
      }))

  const activityPages: MetadataRoute.Sitemap = activitiesResult.error
    ? []
    : (activitiesResult.data ?? []).map((row) => ({
        url: `${siteUrl}/activities/${activitySlug({ id: String(row.id), title: String(row.title ?? "Family activity") })}`,
        lastModified: row.last_seen_at ? new Date(String(row.last_seen_at)) : undefined,
        changeFrequency: "weekly" as const,
        priority: 0.7,
      }))

  return [...staticPages, ...eventPages, ...activityPages]
}

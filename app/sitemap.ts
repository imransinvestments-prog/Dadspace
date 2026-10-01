import type { MetadataRoute } from "next"
import { siteUrl } from "@/lib/seo"

export default function sitemap(): MetadataRoute.Sitemap {
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

  return pages.map(({ path, changeFrequency, priority }) => ({
    url: `${siteUrl}${path}`,
    lastModified: now,
    changeFrequency,
    priority,
  }))
}

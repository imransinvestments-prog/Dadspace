import type { MetadataRoute } from "next"

const base = "https://dadspace.vercel.app"

export default function sitemap(): MetadataRoute.Sitemap {
  const pages = ["", "/events", "/forum", "/news", "/deals"]

  return pages.map((path) => ({
    url: `${base}${path}`,
    lastModified: new Date(),
    changeFrequency: "daily",
    priority: path === "" ? 1 : 0.8,
  }))
}

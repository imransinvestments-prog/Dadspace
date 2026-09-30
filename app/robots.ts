import type { MetadataRoute } from "next"

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/profile", "/api/"],
    },
    sitemap: "https://dadspace.vercel.app/sitemap.xml",
  }
}

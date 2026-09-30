import type { MetadataRoute } from "next"
import { isProduction, siteUrl } from "@/lib/seo"

export default function robots(): MetadataRoute.Robots {
  if (!isProduction) {
    return {
      rules: { userAgent: "*", disallow: "/" },
    }
  }

  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/profile", "/api/"],
    },
    sitemap: `${siteUrl}/sitemap.xml`,
  }
}

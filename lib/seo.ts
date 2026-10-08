import type { Metadata } from "next"

const canonicalSiteUrl = "https://www.dad-space.co.uk"

// The public custom domain is the canonical SEO origin. NEXT_PUBLIC_SITE_URL
// can still override it deliberately for another production deployment.
export const siteUrl = (process.env.NEXT_PUBLIC_SITE_URL || canonicalSiteUrl).replace(/\/$/, "")
export const isProduction = process.env.VERCEL_ENV ? process.env.VERCEL_ENV === "production" : process.env.NODE_ENV === "production"

export const siteName = "Dadspace"
export const defaultTitle = "Dadspace – family days out for UK dads"
export const defaultDescription =
  "Find UK family days out, local activities, parenting news and useful deals on baby and kids' kit."

export function pageMetadata(
  title: string,
  path: string,
  description: string,
  options?: { image?: string; noIndex?: boolean },
): Metadata {
  const canonical = new URL(path || "/", siteUrl).toString()
  const image = options?.image || "/images/hero-dad.png"
  const noIndex = !isProduction || options?.noIndex === true

  return {
    title,
    description,
    alternates: { canonical },
    robots: noIndex ? { index: false, follow: false } : { index: true, follow: true },
    openGraph: {
      title,
      description,
      url: canonical,
      siteName,
      locale: "en_GB",
      type: "website",
      images: [{ url: image, width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [image],
    },
  }
}

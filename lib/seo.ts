import type { Metadata } from "next"

const fallbackUrl = "https://dadspace.vercel.app"

export const siteUrl = (process.env.NEXT_PUBLIC_SITE_URL || fallbackUrl).replace(/\/$/, "")
export const isProduction = process.env.VERCEL_ENV === "production" || process.env.NODE_ENV === "production"

export const siteName = "Dadspace"
export const defaultTitle = "Dadspace – the hub for UK dads"
export const defaultDescription =
  "Find family days out near you, chat with other dads, catch up on dad rights and parenting news, and grab deals on baby and kids' kit."

export function pageMetadata(
  title: string,
  path: string,
  description: string,
  options?: { image?: string; noIndex?: boolean },
): Metadata {
  const canonical = new URL(path || "/", siteUrl).toString()
  const image = options?.image || "/images/hero-dad.png"
  const noIndex = options?.noIndex ?? !isProduction

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

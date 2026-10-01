import { defaultDescription, siteName, siteUrl } from "@/lib/seo"

export function absoluteUrl(src: string) {
  return src.startsWith("http") ? src : `${siteUrl}${src.startsWith("/") ? "" : "/"}${src}`
}

export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      // JSON.stringify output with "<" escaped cannot break out of the script tag.
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  )
}

export function SiteJsonLd() {
  return (
    <JsonLd
      data={{
        "@context": "https://schema.org",
        "@graph": [
          {
            "@type": "Organization",
            "@id": `${siteUrl}/#organization`,
            name: siteName,
            url: siteUrl,
            logo: absoluteUrl("/icon-512.png"),
            description: defaultDescription,
            areaServed: { "@type": "Country", name: "United Kingdom" },
          },
          {
            "@type": "WebSite",
            "@id": `${siteUrl}/#website`,
            name: siteName,
            url: siteUrl,
            description: defaultDescription,
            inLanguage: "en-GB",
            publisher: { "@id": `${siteUrl}/#organization` },
            audience: { "@type": "ParentAudience", audienceType: "Dads and fathers in the UK" },
          },
        ],
      }}
    />
  )
}

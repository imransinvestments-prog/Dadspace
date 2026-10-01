import { JsonLd, absoluteUrl } from "@/components/seo/json-ld"
import { CATEGORY_LABELS, type NewsItem } from "@/lib/news"
import { newsImageFor } from "@/lib/news-images"
import { siteUrl } from "@/lib/seo"

export function NewsJsonLd({ items }: { items: NewsItem[] }) {
  const articles = items.filter((item) => item.url)

  return (
    <JsonLd
      data={{
        "@context": "https://schema.org",
        "@graph": [
          {
            "@type": "CollectionPage",
            "@id": `${siteUrl}/news#page`,
            url: `${siteUrl}/news`,
            name: "UK news for dads",
            description: "UK news that matters to dads, each story summarised with why it matters to fathers and families.",
            inLanguage: "en-GB",
            isPartOf: { "@id": `${siteUrl}/#website` },
            mainEntity: { "@id": `${siteUrl}/news#list` },
          },
          {
            "@type": "ItemList",
            "@id": `${siteUrl}/news#list`,
            numberOfItems: articles.length,
            itemListElement: articles.map((item, i) => ({
              "@type": "ListItem",
              position: i + 1,
              item: {
                "@type": "NewsArticle",
                headline: item.title.slice(0, 110),
                url: item.url,
                datePublished: item.published_at || undefined,
                description: item.summary || undefined,
                abstract: item.why_it_matters ? `Why it matters to dads: ${item.why_it_matters}` : undefined,
                articleSection: item.category ? CATEGORY_LABELS[item.category] ?? item.category : undefined,
                image: [absoluteUrl(newsImageFor(item.category, item.id))],
                publisher: item.source_name ? { "@type": "Organization", name: item.source_name } : undefined,
                inLanguage: "en-GB",
              },
            })),
          },
        ],
      }}
    />
  )
}

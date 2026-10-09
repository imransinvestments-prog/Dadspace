import { NewsFeed } from "@/components/news/news-feed"
import { NewsJsonLd } from "@/components/news/news-json-ld"
import { fetchNews, newsCategory, type NewsItem } from "@/lib/news"
import { pageMetadata } from "@/lib/seo"

export const metadata = pageMetadata(
  "News",
  "/news",
  "UK news that matters to dads, summarised with why it matters.",
  {image:"/images/news/parenting.png"},
)

// Re-check the database for new articles at most every 10 minutes.
export const revalidate = 600

export default async function NewsPage({ searchParams }: { searchParams: Promise<{ category?: string | string[] }> }) {
  const category = newsCategory((await searchParams).category)
  // Fetch the first 20 articles on the server so the page shows up instantly.
  // If this fails, the browser will try again and show a retry button if needed.
  let initialItems: NewsItem[] | null = null
  try {
    initialItems = await fetchNews({ region: "all", category, page: 0 })
  } catch {
    initialItems = null
  }

  return (
    <>
      {initialItems?.length ? <NewsJsonLd items={initialItems} /> : null}
      <NewsFeed key={category} initialItems={initialItems} initialCategory={category} />
    </>
  )
}

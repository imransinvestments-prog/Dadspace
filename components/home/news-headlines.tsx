import Link from "next/link"
import { EmptyState } from "@/components/empty-state"
import { CATEGORY_LABELS } from "@/lib/news"
import { SectionHeader } from "./section-header"
import type { Article, HomeData } from "@/lib/types"

const cardClass =
  "flex flex-col gap-1 rounded-lg border bg-card p-4 transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-navy/10"

function HeadlineBody({ article }: { article: Article }) {
  const categoryLabel = article.category ? (CATEGORY_LABELS[article.category] ?? article.category) : null
  return (
    <>
      <span className="flex flex-wrap items-center gap-x-2 text-xs font-bold tracking-wide uppercase">
        {categoryLabel && <span className="text-primary">{categoryLabel}</span>}
        {article.source && <span className="text-muted-foreground">{article.source}</span>}
      </span>
      <p className="leading-snug font-semibold text-pretty">{article.title}</p>
    </>
  )
}

export function NewsHeadlines({ articles }: { articles: HomeData["articles"] }) {
  return (
    <section aria-labelledby="news-title" className="flex flex-col gap-4">
      <SectionHeader id="news-title" title="Latest headlines" href="/news" linkLabel="News" isSample={articles.isSample} />
      {articles.items.length ? (
        <ul className="flex flex-col gap-3">
          {articles.items.map((article) => (
            <li key={article.id}>
              {article.url ? (
                <a href={article.url} target="_blank" rel="noopener noreferrer" className={cardClass}>
                  <HeadlineBody article={article} />
                  <span className="sr-only">(opens in a new tab)</span>
                </a>
              ) : (
                <Link href="/news" className={cardClass}>
                  <HeadlineBody article={article} />
                </Link>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState title="No news is good news." body="Or the feed's having a lie-in." />
      )}
    </section>
  )
}

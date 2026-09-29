import Link from "next/link"
import { EmptyState } from "@/components/empty-state"
import { SectionHeader } from "./section-header"
import type { HomeData } from "@/lib/types"

export function NewsHeadlines({ articles }: { articles: HomeData["articles"] }) {
  return (
    <section aria-labelledby="news-title" className="flex flex-col gap-4">
      <SectionHeader id="news-title" title="Latest headlines" href="/news" linkLabel="News" isSample={articles.isSample} />
      {articles.items.length ? (
        <ul className="flex flex-col gap-3">
          {articles.items.map((article) => (
            <li key={article.id}>
              <Link href="/news" className="flex flex-col gap-1 rounded-lg border bg-card p-4 transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-navy/10">
                {article.source && <span className="text-xs font-bold tracking-wide text-primary uppercase">{article.source}</span>}
                <p className="leading-snug font-semibold text-pretty">{article.title}</p>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState title="No news is good news." body="Or the feed's having a lie-in." />
      )}
    </section>
  )
}

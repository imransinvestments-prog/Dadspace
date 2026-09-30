"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { EmptyState } from "@/components/empty-state"
import { CATEGORY_LABELS } from "@/lib/news"
import { SectionHeader } from "./section-header"
import type { Article, HomeData } from "@/lib/types"

const ROTATE_MS = 30_000

const cardClass =
  "flex flex-col gap-1 rounded-lg border bg-card p-4 transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-navy/10"

function HeadlineBody({ article }: { article: Article }) {
  const categoryLabel = article.category ? (CATEGORY_LABELS[article.category] ?? article.category) : null
  return (
    <span key={article.id} className="animate-fade flex flex-col gap-1">
      <span className="flex flex-wrap items-center gap-x-2 text-xs font-bold tracking-wide uppercase">
        {categoryLabel && <span className="text-primary">{categoryLabel}</span>}
        {article.source && <span className="text-muted-foreground">{article.source}</span>}
      </span>
      <span className="leading-snug font-semibold text-pretty">{article.title}</span>
    </span>
  )
}

function useRotationTick(enabled: boolean, paused: boolean) {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    if (!enabled || paused) return
    const id = window.setInterval(() => {
      if (document.visibilityState === "visible") setTick((t) => t + 1)
    }, ROTATE_MS)
    return () => window.clearInterval(id)
  }, [enabled, paused])
  return tick
}

export function NewsHeadlines({ articles }: { articles: HomeData["articles"] }) {
  const pool = articles.pool ?? articles.items.map((article) => [article])
  const canRotate = pool.some((list) => list.length > 1)
  const [paused, setPaused] = useState(false)
  const tick = useRotationTick(canRotate, paused)
  const current = pool.map((list) => list[tick % list.length])

  return (
    <section aria-labelledby="news-title" className="flex flex-col gap-4">
      <SectionHeader id="news-title" title="Latest headlines" href="/news" linkLabel="News" isSample={articles.isSample} />
      {current.length ? (
        <ul
          className="flex flex-col gap-3"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
          onFocus={() => setPaused(true)}
          onBlur={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget)) setPaused(false)
          }}
        >
          {current.map((article, slot) => (
            <li key={slot}>
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

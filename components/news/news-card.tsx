import { ArrowUpRight } from "lucide-react"
import { timeAgo } from "@/lib/dates"
import { CATEGORY_LABELS, REGION_LABELS, type NewsItem } from "@/lib/news"

/**
 * One article. The whole card links out to the original story in a new tab.
 * We only show a short summary; people read the full story on the source site.
 */
export function NewsCard({ item }: { item: NewsItem }) {
  const ago = timeAgo(item.published_at)
  const showRegion = item.region && item.region !== "uk"

  const content = (
    <>
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-heading text-lg leading-snug font-bold text-pretty line-clamp-3">{item.title}</h2>
        {item.url && <ArrowUpRight aria-hidden="true" className="mt-1 size-4 shrink-0 text-muted-foreground" />}
      </div>

      <p className="flex flex-wrap items-center gap-x-2 text-sm text-muted-foreground">
        {item.source_name && <span className="font-semibold text-foreground">{item.source_name}</span>}
        {item.source_name && ago && <span aria-hidden="true">·</span>}
        {ago && item.published_at && (
          // The label can differ by a minute between server and browser, which is harmless.
          <time dateTime={item.published_at} suppressHydrationWarning>
            {ago}
          </time>
        )}
      </p>

      {item.why_it_matters && (
        <p className="truncate rounded-md bg-highlight px-3 py-2 text-sm font-medium text-highlight-foreground" title={item.why_it_matters}>
          <span className="font-bold">Why it matters: </span>
          {item.why_it_matters}
        </p>
      )}

      {item.summary && <p className="text-sm leading-relaxed text-muted-foreground line-clamp-2">{item.summary}</p>}

      <div className="flex flex-wrap gap-2">
        {item.category && (
          <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold text-foreground">
            {CATEGORY_LABELS[item.category] ?? item.category}
          </span>
        )}
        {showRegion && (
          <span className="rounded-full border px-2.5 py-0.5 text-xs font-semibold text-accent">
            {REGION_LABELS[item.region as string] ?? item.region}
          </span>
        )}
      </div>
    </>
  )

  const className =
    "flex flex-col gap-3 rounded-lg border bg-card p-5 text-card-foreground transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-navy/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"

  if (!item.url) return <article className={className}>{content}</article>

  return (
    <a href={item.url} target="_blank" rel="noopener noreferrer" className={className}>
      {content}
      <span className="sr-only">(opens the original story in a new tab)</span>
    </a>
  )
}

import { ArrowUpRight } from "lucide-react"
import type { NewsItem } from "@/lib/types"

const dateFormatter = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  timeZone: "Europe/London",
})

function formatPublished(value: string | null) {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  const hours = Math.floor((Date.now() - date.getTime()) / 3_600_000)
  if (hours < 1) return "Just now"
  if (hours < 24) return `${hours}h ago`
  if (hours < 48) return "Yesterday"
  return dateFormatter.format(date)
}

export function NewsCard({ item }: { item: NewsItem }) {
  const published = formatPublished(item.published_at)
  const meta = [item.source_name, published].filter(Boolean).join(" · ")

  const body = (
    <>
      <div className="flex items-center justify-between gap-3">
        {item.category && <span className="text-xs font-bold tracking-wide text-primary uppercase">{item.category}</span>}
        {item.url && <ArrowUpRight aria-hidden="true" className="size-4 shrink-0 text-muted-foreground" />}
      </div>
      <h2 className="font-heading text-lg leading-snug font-bold text-pretty">{item.title}</h2>
      {item.summary && <p className="text-sm leading-relaxed text-muted-foreground line-clamp-3">{item.summary}</p>}
      {item.why_it_matters && (
        <p className="rounded-md bg-muted p-3 text-sm leading-relaxed">
          <span className="font-semibold">Why it matters: </span>
          {item.why_it_matters}
        </p>
      )}
      {meta && <p className="mt-auto text-xs text-muted-foreground">{meta}</p>}
    </>
  )

  const className =
    "flex h-full flex-col gap-3 rounded-lg border bg-card p-5 transition hover:-translate-y-0.5 hover:shadow-lg hover:shadow-navy/10"

  return item.url ? (
    <a href={item.url} target="_blank" rel="noopener noreferrer" className={className}>
      {body}
      <span className="sr-only">(opens in a new tab)</span>
    </a>
  ) : (
    <article className={className}>{body}</article>
  )
}

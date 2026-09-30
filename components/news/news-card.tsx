import Image from "next/image"
import { ArrowUpRight, MapPin, Zap } from "lucide-react"
import { timeAgo } from "@/lib/dates"
import { CATEGORY_LABELS, REGION_LABELS, type NewsItem } from "@/lib/news"
import { newsImageFor } from "@/lib/news-images"
import { cn } from "@/lib/utils"

export type NewsCardVariant = "hero" | "tile" | "wide"

/**
 * One article. The whole card links out to the original story in a new tab.
 * - "hero": the big featured card at the top, text over the photo.
 * - "tile": a vertical card with the photo on top (the default in the grid).
 * - "wide": a horizontal card that spans both grid columns, to break up the rhythm.
 */
export function NewsCard({ item, variant = "tile", priority = false }: { item: NewsItem; variant?: NewsCardVariant; priority?: boolean }) {
  const ago = timeAgo(item.published_at)
  const category = item.category ? (CATEGORY_LABELS[item.category] ?? item.category) : null
  const region = item.region && item.region !== "uk" ? (REGION_LABELS[item.region] ?? item.region) : null
  const image = newsImageFor(item.category, item.id)
  const isHero = variant === "hero"

  const tags = (category || region) && (
    <div className="flex flex-wrap items-center gap-2">
      {category && (
        <span
          className={cn(
            "rounded-full px-2.5 py-1 text-xs font-bold tracking-wide uppercase",
            isHero ? "bg-primary text-primary-foreground" : "bg-primary/15 text-primary",
          )}
        >
          {category}
        </span>
      )}
      {region && (
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold",
            isHero ? "bg-navy/60 text-navy-foreground backdrop-blur-sm" : "bg-accent/15 text-accent",
          )}
        >
          <MapPin className="size-3" aria-hidden="true" />
          {region}
        </span>
      )}
    </div>
  )

  const meta = (
    <p className={cn("flex flex-wrap items-center gap-x-2 text-xs", isHero ? "text-navy-foreground/80" : "text-muted-foreground")}>
      {item.source_name && <span className="font-semibold">{item.source_name}</span>}
      {item.source_name && ago && <span aria-hidden="true">·</span>}
      {ago && item.published_at && (
        // The label can differ by a minute between server and browser, which is harmless.
        <time dateTime={item.published_at} suppressHydrationWarning>
          {ago}
        </time>
      )}
    </p>
  )

  const tldr = item.why_it_matters && (
    <div
      className={cn(
        "flex items-start gap-2 rounded-md border-l-4 border-highlight px-3 py-2 text-sm leading-relaxed",
        isHero ? "bg-navy/60 text-navy-foreground backdrop-blur-sm" : "bg-muted/60 text-foreground",
      )}
    >
      <Zap className="mt-0.5 size-4 shrink-0 fill-highlight text-highlight" aria-hidden="true" />
      <p className={cn(!isHero && "line-clamp-2")}>
        <span className="sr-only">Why it matters: </span>
        {item.why_it_matters}
      </p>
    </div>
  )

  const content = isHero ? (
    <>
      <Image
        src={image}
        alt=""
        fill
        priority={priority}
        sizes="(min-width: 1024px) 60rem, 100vw"
        className="object-cover transition duration-500 group-hover:scale-105"
      />
      <div aria-hidden="true" className="absolute inset-0 bg-gradient-to-t from-navy via-navy/70 to-navy/0" />
      <div className="relative flex flex-col gap-3 p-5 md:max-w-3xl md:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-highlight px-2.5 py-1 text-xs font-bold tracking-wide text-highlight-foreground uppercase">
            Top story
          </span>
          {tags}
        </div>
        <h2 className="font-heading text-2xl leading-tight font-extrabold text-balance text-navy-foreground md:text-4xl">{item.title}</h2>
        {meta}
        {tldr}
      </div>
    </>
  ) : (
    <>
      <div className={cn("relative overflow-hidden bg-muted", variant === "wide" ? "aspect-video md:aspect-auto md:w-2/5 md:shrink-0" : "aspect-video")}>
        <Image
          src={image}
          alt=""
          fill
          sizes={variant === "wide" ? "(min-width: 768px) 24rem, 100vw" : "(min-width: 768px) 30rem, 100vw"}
          className="object-cover transition duration-500 group-hover:scale-105"
        />
      </div>
      <div className="flex flex-1 flex-col gap-3 p-5">
        <div className="flex items-start justify-between gap-3">
          {tags ?? <span />}
          {item.url && (
            <ArrowUpRight
              aria-hidden="true"
              className="size-5 shrink-0 text-muted-foreground transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-primary"
            />
          )}
        </div>
        <h2 className={cn("font-heading leading-snug font-extrabold text-pretty", variant === "wide" ? "text-xl md:text-2xl" : "text-lg line-clamp-3")}>
          {item.title}
        </h2>
        {meta}
        {tldr}
        {variant === "wide" && item.summary && <p className="text-sm leading-relaxed text-muted-foreground line-clamp-2">{item.summary}</p>}
      </div>
    </>
  )

  const className = cn(
    "group relative flex h-full overflow-hidden rounded-xl border text-card-foreground transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    isHero ? "min-h-96 flex-col justify-end border-transparent md:min-h-[28rem]" : "flex-col bg-card hover:-translate-y-1 hover:shadow-xl hover:shadow-navy/15",
    variant === "wide" && "md:flex-row",
  )

  if (!item.url) return <article className={className}>{content}</article>

  return (
    <a href={item.url} target="_blank" rel="noopener noreferrer" className={className}>
      {content}
      <span className="sr-only">(opens the original story in a new tab)</span>
    </a>
  )
}

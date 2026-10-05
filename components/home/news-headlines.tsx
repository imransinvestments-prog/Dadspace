import { CATEGORY_LABELS } from "@/lib/news"
import { SectionHeader } from "./section-header"
import type { HomeData } from "@/lib/types"

export function NewsHeadlines({ articles }: { articles: HomeData["articles"] }) {
  return <section aria-labelledby="news-title" className="flex flex-col gap-4">
    <SectionHeader id="news-title" title="Latest news" href="/news" linkLabel="View all news" isSample={articles.isSample}/>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {articles.items.slice(0,8).map(article => <article key={article.id} className="flex min-w-0 flex-col gap-3 rounded-xl border bg-card p-5">
        <p className="text-xs font-bold uppercase tracking-wide text-accent">{CATEGORY_LABELS[article.category ?? "other"] ?? article.category}</p>
        <h3 className="font-heading text-lg font-bold leading-snug"><a href={article.url || "/news"} target={article.url ? "_blank" : undefined} rel="noopener noreferrer" className="hover:underline">{article.title}</a></h3>
        <p className="text-xs text-muted-foreground">{article.source}{article.published_at && <span> · {new Intl.DateTimeFormat("en-GB",{day:"numeric",month:"short",timeZone:"Europe/London"}).format(new Date(article.published_at))}</span>}</p>
        {article.summary?.trim() && <p className="text-sm leading-relaxed text-muted-foreground">{article.summary}</p>}
        {article.why_it_matters?.trim() && <div className="rounded-md border-l-4 border-highlight bg-muted/60 px-3 py-2 text-sm leading-relaxed">
          <p className="mb-1 text-xs font-bold uppercase tracking-wide">Why it matters</p>
          <p>{article.why_it_matters}</p>
        </div>}
        <a className="mt-auto pt-2 text-sm font-semibold text-accent hover:underline" href={article.url || "/news"} target={article.url ? "_blank" : undefined} rel="noopener noreferrer">Read article<span className="sr-only">{article.url ? " (opens in a new tab)" : ""}</span> →</a>
      </article>)}
    </div>
    {!articles.items.length && <p className="text-muted-foreground">News is temporarily unavailable.</p>}
  </section>
}

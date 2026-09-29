import Link from "next/link"
import { MessageCircle } from "lucide-react"
import { EmptyState } from "@/components/empty-state"
import { SectionHeader } from "./section-header"
import type { HomeData } from "@/lib/types"

export function TrendingThreads({ threads }: { threads: HomeData["threads"] }) {
  return (
    <section aria-labelledby="trending-title" className="flex flex-col gap-4">
      <SectionHeader id="trending-title" title="Trending in the forum" href="/forum" linkLabel="Forum" isSample={threads.isSample} />
      {threads.items.length ? (
        <ol className="flex flex-col overflow-hidden rounded-lg border bg-card">
          {threads.items.map((thread) => (
            <li key={thread.id} className="border-b last:border-b-0">
              <Link href="/forum" className="flex items-center gap-4 p-4 transition hover:bg-muted">
                <div className="flex min-w-0 flex-1 flex-col gap-1.5">
                  {thread.category && <span className="text-xs font-bold tracking-wide text-accent uppercase">{thread.category}</span>}
                  <p className="leading-snug font-semibold text-pretty">{thread.title}</p>
                  {thread.author && <p className="text-xs text-muted-foreground">by {thread.author}</p>}
                </div>
                <span className="flex shrink-0 items-center gap-1.5 rounded-full bg-muted px-3 py-1.5 text-sm font-semibold">
                  <MessageCircle className="size-4 text-primary" aria-hidden />
                  {thread.comments}
                  <span className="sr-only">comments</span>
                </span>
              </Link>
            </li>
          ))}
        </ol>
      ) : (
        <EmptyState title="Tumbleweed." body="Nobody's posted yet. Be the dad who breaks the ice." />
      )}
    </section>
  )
}

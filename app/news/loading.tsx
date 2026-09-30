import { NewsSkeleton } from "@/components/news/news-skeleton"

export default function NewsLoading() {
  return (
    <div className="flex flex-col gap-6">
      <div className="h-10 w-64 animate-pulse rounded bg-muted" />
      <div className="h-10 w-full animate-pulse rounded-full bg-muted" />
      <NewsSkeleton />
    </div>
  )
}

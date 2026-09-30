/** Grey placeholder cards shown while articles are loading, in the same shape as the real feed. */
export function NewsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="flex flex-col gap-4" aria-hidden="true">
      <div className="h-96 animate-pulse rounded-xl bg-muted md:h-[28rem]" />
      <ul className="grid gap-4 md:grid-cols-2">
        {Array.from({ length: count }, (_, i) => (
          <li key={i} className="flex animate-pulse flex-col overflow-hidden rounded-xl border bg-card">
            <div className="aspect-video bg-muted" />
            <div className="flex flex-col gap-3 p-5">
              <div className="h-5 w-20 rounded-full bg-muted" />
              <div className="h-5 w-11/12 rounded bg-muted" />
              <div className="h-5 w-2/3 rounded bg-muted" />
              <div className="h-12 w-full rounded-md bg-muted" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

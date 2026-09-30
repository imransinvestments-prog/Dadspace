/** Grey placeholder cards shown while articles are loading. */
export function NewsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <ul className="flex flex-col gap-3" aria-hidden="true">
      {Array.from({ length: count }, (_, i) => (
        <li key={i} className="flex animate-pulse flex-col gap-3 rounded-lg border bg-card p-5">
          <div className="h-5 w-11/12 rounded bg-muted" />
          <div className="h-5 w-2/3 rounded bg-muted" />
          <div className="h-4 w-1/3 rounded bg-muted" />
          <div className="h-9 w-full rounded-md bg-muted" />
          <div className="h-4 w-4/5 rounded bg-muted" />
        </li>
      ))}
    </ul>
  )
}

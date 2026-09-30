export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-lg border border-dashed px-6 py-10 text-center">
      <p className="font-heading text-lg font-bold">{title}</p>
      <p className="text-sm leading-relaxed text-muted-foreground">{body}</p>
    </div>
  )
}

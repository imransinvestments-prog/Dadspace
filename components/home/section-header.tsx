import Link from "next/link"
import { ArrowRight } from "lucide-react"

export function SectionHeader({
  id,
  title,
  href,
  linkLabel,
  isSample,
}: {
  id: string
  title: string
  href: string
  linkLabel: string
  isSample?: boolean
}) {
  return (
    <div className="flex items-end justify-between gap-4">
      <div className="flex items-center gap-2">
        <h2 id={id} className="font-heading text-2xl font-extrabold tracking-tight text-balance">
          {title}
        </h2>
        {isSample && <SampleBadge />}
      </div>
      <Link href={href} className="inline-flex shrink-0 items-center gap-1 rounded-full py-2 text-sm font-semibold text-accent hover:underline">
        {linkLabel}
        <ArrowRight className="size-4" aria-hidden />
      </Link>
    </div>
  )
}

export function SampleBadge() {
  return (
    <span
      className="rounded-full border border-dashed px-2 py-0.5 text-xs font-medium text-muted-foreground"
      title="Nothing in the database yet, so this is example content"
    >
      Sample
    </span>
  )
}

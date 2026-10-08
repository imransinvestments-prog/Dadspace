import Image from "next/image"
import { Sparkles } from "lucide-react"
import { categoryImage, categoryPlural } from "@/lib/venue-meta"
import { cn } from "@/lib/utils"

type Props = {
  categories: { key: string; count: number }[]
  total: number
  selected: string
  onSelect: (key: string) => void
}

const tile = (active: boolean) =>
  cn(
    "group relative flex h-36 w-32 shrink-0 snap-start flex-col justify-end overflow-hidden rounded-xl p-3 text-left transition md:h-40 md:w-36",
    "focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-ring",
    active ? "-translate-y-1 ring-4 ring-primary" : "hover:-translate-y-1",
  )

export function CategoryRail({ categories, total, selected, onSelect }: Props) {
  return (
    <div className="-mx-4 flex snap-x gap-3 overflow-x-auto px-4 pt-2 pb-3 md:-mx-8 md:px-8" role="group" aria-label="Venue type">
      <button type="button" aria-pressed={selected === "all"} onClick={() => onSelect("all")} className={cn(tile(selected === "all"), "bg-navy text-navy-foreground")}>
        <Sparkles className="absolute top-3 left-3 size-6 text-highlight transition group-hover:rotate-12" aria-hidden />
        <span className="font-heading text-lg leading-tight font-extrabold">Everything</span>
        <span className="text-xs font-semibold opacity-80">{total} places</span>
      </button>

      {categories.map(({ key, count }) => (
        <button key={key} type="button" aria-pressed={selected === key} onClick={() => onSelect(key)} className={tile(selected === key)}>
          <Image
            src={categoryImage(key) || "/placeholder.svg"}
            alt=""
            fill
            quality={60}
            sizes="144px"
            className="object-cover transition duration-500 group-hover:scale-110"
          />
          <span className="absolute inset-0 bg-gradient-to-t from-navy via-navy/30 to-transparent" aria-hidden />
          <span className="relative font-heading text-base leading-tight font-extrabold text-navy-foreground text-balance">
            {categoryPlural(key)}
          </span>
          <span className="relative text-xs font-semibold text-navy-foreground/80">{count} places</span>
        </button>
      ))}
    </div>
  )
}

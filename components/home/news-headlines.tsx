import Link from "next/link"
import { ArrowUpRight, Baby, BookOpen, Heart, HeartPulse, Landmark, Newspaper, ShieldCheck, Trees, Wallet } from "lucide-react"
import type { HomeData } from "@/lib/types"

const sections = [
  { category: "safety", title: "Child safety", icon: ShieldCheck, note: "Keeping little ones safe" },
  { category: "parenting", title: "Parenting report", icon: Baby, note: "For the everyday dad" },
  { category: "wellbeing", title: "Wellbeing", icon: Heart, note: "A little time for you" },
  { category: "health", title: "Family health", icon: HeartPulse, note: "Looking after the family" },
  { category: "activities", title: "Days out & play", icon: Trees, note: "Adventures start here" },
  { category: "money", title: "Money matters", icon: Wallet, note: "Making the budget go further" },
  { category: "education", title: "Education", icon: BookOpen, note: "Growing curious minds" },
  { category: "policy", title: "Policy & change", icon: Landmark, note: "The decisions that affect dads" },
  { category: "other", title: "Elsewhere", icon: Newspaper, note: "More from the news desk" },
] as const

export function NewsHeadlines({ monthlyNews }: { monthlyNews: HomeData["monthlyNews"] }) {
  return <section aria-labelledby="news-title" className="dad-newspaper p-4 sm:p-6 lg:p-8">
    <div className="flex flex-wrap justify-between gap-2 border-y-2 border-current py-2 text-xs font-bold uppercase tracking-wider">
      <span>{monthlyNews.month} edition</span><span>News for UK dads · Monthly digest</span>
    </div>
    <header className="border-b-4 border-double border-current pb-4 pt-5 text-center">
      <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.3em]">Family life, freshly reported</p>
      <h2 id="news-title" className="font-serif text-[clamp(2.1rem,6vw,5.5rem)] font-black uppercase leading-[0.95] tracking-tight">The Dad Space Times</h2>
      <p className="mt-3 text-sm sm:text-base">Your month in news. Pick a section. Find your next read.</p>
    </header>
    <div className="my-3 bg-[#252119] px-3 py-2 text-center text-xs font-bold uppercase tracking-[0.15em] text-[#f6eedb]">The news desk · Articles collected this month</div>
    {!monthlyNews.counts && <p role="status" className="border-b border-current py-3 text-center text-sm">Monthly counts are temporarily unavailable. You can still browse every section.</p>}
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4">
      {sections.map(({ category, title, icon: Icon, note }, index) => {
        const count = monthlyNews.counts?.[category]
        return <Link key={category} href={`/news?category=${category}`} className={`group flex min-w-0 flex-col border-b border-[#252119]/50 px-4 py-5 transition-colors hover:bg-[#252119]/[0.07] focus-visible:z-10 focus-visible:outline-2 focus-visible:outline-offset-[-4px] focus-visible:outline-[#252119] sm:odd:border-r xl:border-r ${index === 8 ? "sm:col-span-2 xl:col-span-4 xl:border-r-0" : ""}`}>
          <h3 className="font-serif text-xl font-black uppercase leading-tight sm:text-2xl">{title}</h3>
          <div className="my-4 flex items-center gap-4">
            <Icon className="size-12 shrink-0 stroke-[1.3]" aria-hidden="true" />
            <span className="font-serif text-6xl font-black leading-none tabular-nums sm:text-7xl">{count === undefined ? "—" : count.toLocaleString("en-GB")}</span>
            <span className="sr-only">{count === undefined ? "Count unavailable" : `${count === 1 ? "article" : "articles"} collected in ${monthlyNews.month}`}</span>
          </div>
          <p className="mb-4 text-xs italic">{note}</p>
          <span className="mt-auto flex items-center justify-between border-t border-current/40 pt-2 text-xs font-bold uppercase tracking-wide">Read the section <ArrowUpRight className="size-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 motion-reduce:transform-none" aria-hidden="true" /></span>
        </Link>
      })}
    </div>
    <footer className="flex flex-wrap items-center justify-between gap-3 border-b-2 border-current py-3 text-xs">
      <p>Relevant, unique stories collected this calendar month. Sections show the latest fortnight.</p>
      <Link href="/news" className="font-bold uppercase underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-4">Browse all news →</Link>
    </footer>
  </section>
}

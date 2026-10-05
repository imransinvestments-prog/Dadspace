import Image from "next/image"
import Link from "next/link"
import { ArrowRight, CalendarHeart } from "lucide-react"

function countdownCopy(sleeps: number) {
  if (sleeps === 0) return { big: "It's the weekend", small: "Snacks packed? Wipes? Spare wipes?" }
  if (sleeps === 1) return { big: "1 sleep", small: "till the weekend. Nearly there." }
  return { big: `${sleeps} sleeps`, small: "till the weekend. Hold the line." }
}

export function HeroGreeting({ greeting, sleeps, weekendLabel }: { greeting: string; sleeps: number; weekendLabel: string }) {
  const copy = countdownCopy(sleeps)

  return (
    <section aria-labelledby="weekend-countdown" className="animate-rise relative isolate min-w-0 overflow-hidden rounded-xl bg-[#12203f] text-[#f5f6fa]">
      <Image
        src="/images/hero-dad.png"
        alt="A dad carrying his laughing daughter on his shoulders through a sunny park"
        fill
        priority
        sizes="(min-width: 1280px) 48vw, (min-width: 768px) 60vw, 100vw"
        className="-z-10 object-cover object-[65%_center]"
      />
      <div className="-z-10 absolute inset-0 bg-[linear-gradient(90deg,#12203f_0%,#12203fe6_35%,#12203f20_100%)]" aria-hidden />

      <div className="flex min-h-[320px] flex-col items-start justify-center gap-7 p-6 sm:min-h-[360px] sm:p-8">
          <p className="text-xs font-bold tracking-wider uppercase">This weekend · {weekendLabel}</p>
          <h2 id="weekend-countdown" className="flex max-w-full flex-col">
            <span className="font-heading text-6xl leading-none font-extrabold tracking-tight text-[#ffc94a] sm:text-7xl">{copy.big}</span>
            <span className="mt-3 text-base leading-snug font-semibold sm:text-lg">{copy.small}</span>
          </h2>
          <span className="sr-only">{greeting}</span>
          <Link
            href="/events"
            className="inline-flex min-h-12 max-w-full items-center gap-2 rounded-full bg-primary px-5 py-3 font-semibold text-primary-foreground transition hover:-translate-y-0.5 hover:shadow-lg"
          >
            <CalendarHeart className="size-5" aria-hidden />
            Plan the weekend
            <ArrowRight className="ml-1 size-4 shrink-0" aria-hidden />
          </Link>
      </div>
    </section>
  )
}

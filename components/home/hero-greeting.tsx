import Image from "next/image"
import Link from "next/link"
import { CalendarHeart } from "lucide-react"

function countdownCopy(sleeps: number) {
  if (sleeps === 0) return { big: "It's the weekend", small: "Snacks packed? Wipes? Spare wipes?" }
  if (sleeps === 1) return { big: "1 sleep", small: "till the weekend. Nearly there." }
  return { big: `${sleeps} sleeps`, small: "till the weekend. Hold the line." }
}

export function HeroGreeting({ greeting, sleeps, weekendLabel }: { greeting: string; sleeps: number; weekendLabel: string }) {
  const copy = countdownCopy(sleeps)

  return (
    <section aria-labelledby="hero-title" className="animate-rise relative isolate overflow-hidden rounded-xl bg-navy text-navy-foreground">
      <Image
        src="/images/hero-dad.png"
        alt="A dad carrying his laughing daughter on his shoulders through a sunny park"
        fill
        priority
        sizes="(min-width: 1024px) 60vw, 100vw"
        className="-z-10 object-cover object-center opacity-70 md:left-auto md:w-3/5 md:opacity-100"
      />
      <div className="-z-10 absolute inset-0 bg-navy/60 md:bg-transparent md:[background:linear-gradient(90deg,var(--navy)_42%,transparent_75%)]" aria-hidden />

      <div className="flex min-h-80 flex-col justify-between gap-8 p-6 md:max-w-md md:p-10">
        <div className="flex flex-col gap-3">
          <p className="text-sm font-semibold tracking-wide text-highlight uppercase">{weekendLabel}</p>
          <h1 id="hero-title" className="font-heading text-4xl leading-none font-extrabold tracking-tight text-balance md:text-5xl">
            {greeting}
          </h1>
        </div>

        <div className="flex flex-col gap-5">
          <p className="flex flex-col">
            <span className="font-heading text-5xl leading-none font-extrabold text-primary md:text-6xl">{copy.big}</span>
            <span className="mt-2 text-base leading-relaxed text-navy-foreground/85">{copy.small}</span>
          </p>
          <Link
            href="/events"
            className="inline-flex h-12 w-fit items-center gap-2 rounded-full bg-primary px-6 font-semibold text-primary-foreground transition hover:-translate-y-0.5 hover:shadow-lg"
          >
            <CalendarHeart className="size-5" aria-hidden />
            Plan the weekend
          </Link>
        </div>
      </div>
    </section>
  )
}

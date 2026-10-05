import Image from "next/image"
import { CalendarHeart, MapPinned, MessageCircleMore } from "lucide-react"
import { DadJoke } from "@/components/home/dad-joke"

export function LaunchComingSoon() {
  return (
    <div className="min-h-dvh bg-[#f5f6fa] text-[#12203f]">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-6 sm:px-10">
        <a href="/" aria-label="Dadspace home" className="flex items-center gap-2.5 rounded-full">
          <Image src="/icon-512.png" alt="" width={36} height={36} className="size-9 rounded-xl" priority />
          <span className="font-heading text-2xl font-extrabold tracking-tight">dad<span className="text-[#ff7a1a]">space</span></span>
        </a>
        <span className="rounded-full border border-[#dde2ee] bg-white px-3 py-2 text-xs font-semibold sm:text-sm">Made for UK dads</span>
      </header>
      <main id="main" className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 pb-8 sm:px-10">
        <section aria-labelledby="coming-soon-title" className="relative isolate overflow-hidden rounded-[28px] bg-[#12203f] text-white">
          <Image src="/images/hero-dad.png" alt="A dad and his daughter enjoying a day out in the park" fill priority sizes="(min-width: 1152px) 1072px, 100vw" className="-z-10 object-cover object-[70%_center]" />
          <div aria-hidden className="absolute inset-0 -z-10 bg-[linear-gradient(90deg,#12203ff5_0%,#12203fe6_40%,#12203f50_100%)]" />
          <div className="flex min-h-[430px] max-w-2xl flex-col justify-center gap-6 p-7 sm:min-h-[480px] sm:p-12">
            <p className="w-fit rounded-full border border-white/25 bg-white/10 px-4 py-2 text-xs font-bold tracking-widest uppercase">Coming soon</p>
            <h1 id="coming-soon-title" className="font-heading text-4xl leading-[1.05] font-extrabold tracking-tight text-balance sm:text-6xl">Good times.<br /><span className="text-[#ffc94a]">Great dad moments.</span></h1>
            <p className="max-w-md text-lg leading-relaxed text-white/90">Your next family adventure starts here.</p>
            <p className="max-w-md text-base leading-relaxed text-white/80">We're getting Dadspace ready: days out, local activities, news and deals for UK dads. A little less planning. A lot more quality time.</p>
            <p className="text-sm font-semibold text-[#ffc94a]">We'll be here when we're ready. Dad jokes included.</p>
          </div>
        </section>
        <div className="grid items-stretch gap-6 md:grid-cols-[minmax(0,1.6fr)_minmax(280px,1fr)]">
          <section aria-labelledby="what-is-coming" className="flex flex-col justify-center gap-6 rounded-xl border border-[#dde2ee] bg-white p-6 sm:p-8">
            <h2 id="what-is-coming" className="font-heading text-2xl font-extrabold tracking-tight">A little more to look forward to.</h2>
            <ul className="flex flex-col gap-6">
              {[
                { icon: CalendarHeart, title: "Weekends worth planning", copy: "Family days out and events, without the endless searching." },
                { icon: MapPinned, title: "Adventures closer to home", copy: "Find venues and activities for your next day together." },
                { icon: MessageCircleMore, title: "A space for dads", copy: "Useful reads, good deals and gloriously bad jokes." },
              ].map(({ icon: Icon, title, copy }) => (
                <li key={title} className="flex items-start gap-4">
                  <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-[#fff0e4]"><Icon className="size-5 text-[#b44a00]" aria-hidden /></span>
                  <div><h3 className="font-heading text-lg font-bold">{title}</h3><p className="mt-1 text-sm leading-relaxed text-[#56627f]">{copy}</p></div>
                </li>
              ))}
            </ul>
          </section>
          <DadJoke />
        </div>
        <footer className="flex flex-wrap items-center justify-between gap-3 text-xs text-[#56627f]">
          <p>Dadspace · Made for UK dads</p>
          <p>Big adventures. Little moments. Coming soon.</p>
        </footer>
      </main>
    </div>
  )
}

import Image from "next/image"
import Link from "next/link"

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2.5 rounded-full" aria-label="Dadspace home">
      <Image src="/icon-512.png" alt="" width={36} height={36} className="size-9 rounded-xl" priority />
      <span className="font-heading text-xl font-extrabold tracking-tight">
        dad<span className="text-primary">space</span>
      </span>
    </Link>
  )
}

import type { Metadata, Viewport } from "next"
import { Bricolage_Grotesque, Plus_Jakarta_Sans } from "next/font/google"
import { ThemeProvider } from "@/components/theme-provider"
import { AppShell } from "@/components/app-shell"
import "./globals.css"

const bricolage = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-bricolage", display: "swap" })
const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-jakarta", display: "swap" })

export const metadata: Metadata = {
  title: { default: "Dadspace – the hub for UK dads", template: "%s · Dadspace" },
  description:
    "Find family days out near you, chat with other dads, catch up on dad rights and parenting news, and grab deals on baby and kids' kit.",
  applicationName: "Dadspace",
  appleWebApp: { capable: true, title: "Dadspace", statusBarStyle: "black-translucent" },
  openGraph: {
    title: "Dadspace – the hub for UK dads",
    description: "Days out, dad chat, news that matters and deals on kids' kit.",
    siteName: "Dadspace",
    locale: "en_GB",
    type: "website",
    images: [{ url: "/images/hero-dad.png", width: 1200, height: 630, alt: "A dad carrying his daughter on his shoulders in a park" }],
  },
  twitter: { card: "summary_large_image" },
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f5f6fa" },
    { media: "(prefers-color-scheme: dark)", color: "#0b1530" },
  ],
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB" suppressHydrationWarning className={`${bricolage.variable} ${jakarta.variable} bg-background`}>
      <body className="font-sans antialiased">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </body>
    </html>
  )
}

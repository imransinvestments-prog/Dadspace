import type { Metadata, Viewport } from "next"
import { Bricolage_Grotesque, Plus_Jakarta_Sans } from "next/font/google"
import { SpeedInsights } from "@vercel/speed-insights/next"
import { ThemeProvider } from "@/components/theme-provider"
import { AppShell } from "@/components/app-shell"
import { LocationProvider } from "@/components/location-provider"
import { LaunchComingSoon } from "@/components/launch-coming-soon"
import { COMING_SOON } from "@/lib/launch"
import { SiteJsonLd } from "@/components/seo/json-ld"
import { defaultDescription, defaultTitle, isProduction, siteName, siteUrl } from "@/lib/seo"
import "./globals.css"

const bricolage = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-bricolage", display: "swap" })
const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-jakarta", display: "swap" })

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: COMING_SOON ? "Dadspace · Coming soon" : defaultTitle, template: "%s · Dadspace" },
  description: COMING_SOON ? "Dadspace is coming soon. Family days out, local activities, news, deals and dad jokes for UK dads." : defaultDescription,
  applicationName: siteName,
  alternates: { canonical: "/" },
  robots: isProduction ? { index: true, follow: true } : { index: false, follow: false },
  appleWebApp: { capable: true, title: siteName, statusBarStyle: "black-translucent" },
  openGraph: {
    title: COMING_SOON ? "Dadspace · Coming soon" : defaultTitle,
    description: "Days out, dad chat, news that matters and deals on kids' kit.",
    url: "/",
    siteName,
    locale: "en_GB",
    type: "website",
    images: [{ url: "/images/hero-dad.png", width: 1200, height: 630, alt: "A dad carrying his daughter on his shoulders in a park" }],
  },
  twitter: {
    card: "summary_large_image",
    title: COMING_SOON ? "Dadspace · Coming soon" : defaultTitle,
    description: defaultDescription,
    images: ["/images/hero-dad.png"],
  },
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
  const publisherId = process.env.AWIN_PUBLISHER_ID?.trim()
  const masterTagEnabled = !COMING_SOON && publisherId && /^[1-9]\d*$/.test(publisherId)
  return (
    <html lang="en-GB" suppressHydrationWarning className={`${bricolage.variable} ${jakarta.variable} bg-background`}>
      <body className="font-sans antialiased">
        <SiteJsonLd />
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          {COMING_SOON ? <LaunchComingSoon /> : <LocationProvider>
            <AppShell>{children}</AppShell>
          </LocationProvider>}
        </ThemeProvider>
        <SpeedInsights />
        {masterTagEnabled && <script src={`https://www.dwin2.com/pub.${publisherId}.min.js`} />}
      </body>
    </html>
  )
}

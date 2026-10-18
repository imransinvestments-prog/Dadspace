import Script from "next/script"

// Only public pages carrying offer links include this component. Next inserts
// afterInteractive scripts into the rendered body without blocking the page.
// Installation does not establish successful delivery or plugin activation.
export function AwinPublisherTag() {
  return <Script id="awin-publisher-mastertag" src="https://www.dwin2.com/pub.3111278.min.js" strategy="afterInteractive" />
}

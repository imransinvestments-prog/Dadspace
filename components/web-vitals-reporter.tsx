"use client"

import { useReportWebVitals } from "next/web-vitals"

type Report = Parameters<Parameters<typeof useReportWebVitals>[0]>[0]

// Module-level so the hook keeps one stable callback across renders.
function send(metric: Report) {
  const body = JSON.stringify({
    name: metric.name, value: metric.value, rating: metric.rating, id: metric.id,
    navigationType: metric.navigationType,
    // Path only: query strings can carry postcodes or sign-in tokens.
    route: window.location.pathname,
  })
  // sendBeacon survives the page being hidden, which is when CLS and INP report.
  if (!navigator.sendBeacon?.("/api/vitals", body)) {
    fetch("/api/vitals", { method: "POST", body, keepalive: true }).catch(() => {})
  }
}

export function WebVitalsReporter() {
  useReportWebVitals(send)
  return null
}

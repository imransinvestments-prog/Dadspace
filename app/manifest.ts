import type { MetadataRoute } from "next"

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Dadspace",
    short_name: "Dadspace",
    description: "The one-stop hub for UK dads: days out, dad chat, news that matters and deals on kids' kit.",
    start_url: "/",
    display: "standalone",
    background_color: "#0b1530",
    theme_color: "#0b1530",
    orientation: "portrait",
    icons: [
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  }
}

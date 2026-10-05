// Export the exact shared display selection for human review, without DB credentials.
// Usage: node scripts/export-deals-review.mjs snapshot.json review-directory
import fs from "node:fs"
import path from "node:path"
import { selectDeals } from "../lib/deals-selection.ts"

const [input, directory] = process.argv.slice(2)
if (!input || !directory) throw new Error("Usage: node scripts/export-deals-review.mjs snapshot.json review-directory")
const rows = JSON.parse(fs.readFileSync(input, "utf8"))
const selected = selectDeals(rows)
const columns = ["rank", "id", "title", "description", "retailer", "price", "was_price", "discount_pct", "link", "expires_at", "last_seen", "audience_evidence", "human_relevant", "human_valuable", "human_terms_clear", "human_link_works", "human_not_expired", "human_savings_supported", "reviewer_notes"]
const escape = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`
const csv = (items) => [columns.join(","), ...items.map((row, index) => columns.map((key) => escape(key === "rank" ? index + 1 : row[key])).join(","))].join("\n") + "\n"
fs.mkdirSync(directory, { recursive: true })
fs.writeFileSync(path.join(directory, "published-review.csv"), csv(selected))
fs.writeFileSync(path.join(directory, "top-20-review.csv"), csv(selected.slice(0, 20)))
console.log(`Exported ${selected.length} eligible offers, ${Math.min(selected.length, 20)} top offers. Labels require a reviewer.`)


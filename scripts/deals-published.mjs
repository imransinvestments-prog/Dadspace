import fs from "node:fs"
import { selectDeals } from "../lib/deals-selection.ts"
const rows = JSON.parse(fs.readFileSync(process.argv[2], "utf8"))
process.stdout.write(JSON.stringify(selectDeals(rows)))

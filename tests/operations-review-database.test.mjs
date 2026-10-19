import test from 'node:test'
import fs from 'node:fs'
import { PGlite } from '@electric-sql/pglite'
test('guarded venue API: permissions, edits, stale guards, import preservation and inverses', async () => {
 const db=new PGlite()
 try {
  for(const path of ['tests/operations-review-fixture.sql','scripts/operations-review.sql','supabase/migrations/20261017102447_operations_review_edit_reject.sql', ...fs.readdirSync('supabase/migrations').filter(p=>p.endsWith('_sprint11_visitor_facts.sql')).map(p=>'supabase/migrations/'+p),'tests/operations-review-transactions.sql','tests/operations-review-edit-transactions.sql','tests/operations-review-visitor-facts.sql']) await db.exec(fs.readFileSync(path,'utf8'))
 } finally { await db.close() }
})

const assert = require('node:assert/strict')
const { test } = require('node:test')
const fs = require('node:fs')
const vm = require('node:vm')
const ts = require('typescript')
function load(file, dependencies = {}, globals = {}) {
  const module = { exports: {} }
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
  vm.runInNewContext(code, { module, exports: module.exports, process: { env: {} }, Intl, Date, Number, Promise, AbortSignal,
    require: name => dependencies[name] ?? require(name), ...globals })
  return module.exports
}
const health = load('lib/operations/health.ts')
const access = load('lib/operations/access.ts')
const owner = '12345678-1234-1234-1234-123456789abc'
const other = '12345678-1234-1234-1234-123456789def'
const ownerUser = { id: owner, email: 'imransinvestments@gmail.com', email_confirmed_at: '2026-10-17T10:00:00Z' }

test('operator identity fails closed and cannot be inferred from metadata or partial ID', () => {
  assert.equal(access.isOperationsUser(owner, undefined), false)
  assert.equal(access.isOperationsUser(owner, 'not-a-uuid'), false)
  assert.equal(access.isOperationsUser(other, owner), false)
  assert.equal(access.isOperationsUser(owner.slice(0, 8), owner), false)
  assert.equal(access.isOperationsUser(owner, ` ${owner.toUpperCase()} `), true)
})
test('email authorization requires an exact confirmed server identity, never profile metadata', () => {
  const user = { email: 'Owner@example.com', email_confirmed_at: '2026-10-14T12:00:00Z' }
  assert.equal(access.isVerifiedOperationsEmail(user, ' owner@example.com '), true)
  assert.equal(access.isVerifiedOperationsEmail(user, undefined), false)
  assert.equal(access.isVerifiedOperationsEmail({ email: user.email }, user.email), false)
  assert.equal(access.isVerifiedOperationsEmail({ ...user, is_anonymous: true }, user.email), false)
  assert.equal(access.isVerifiedOperationsEmail({ ...user, email: 'other@example.com' }, user.email), false)
  assert.equal(access.isVerifiedOperationsEmail({ ...user, email: 'owner@example.com.evil' }, user.email), false)
  assert.equal(access.isVerifiedOperationsEmail({ ...user, email_confirmed_at: 'invalid' }, user.email), false)
})
test('next scheduled UK run handles DST changes and year boundaries', () => {
  assert.equal(health.nextLondonRun(new Date('2026-10-14T06:00:00Z')), '2026-10-14T06:17:00.000Z')
  assert.equal(health.nextLondonRun(new Date('2026-10-24T18:18:00Z')), '2026-10-25T07:17:00.000Z')
  assert.equal(health.nextLondonRun(new Date('2026-03-28T19:18:00Z')), '2026-03-29T06:17:00.000Z')
  assert.equal(health.nextLondonRun(new Date('2026-12-31T20:00:00Z')), '2027-01-01T07:17:00.000Z')
})
const run = { id: 1, event: 'schedule', status: 'completed', conclusion: 'failure', created_at: '2026-10-14T06:56:00Z', updated_at: '2026-10-14T07:15:00Z', html_url: 'https://github.com/imransinvestments-prog/Dadspace/actions/runs/1' }
test('aggregate failure cannot mislabel successful feed; skipped and unavailable are distinct', () => {
  const observation = { run, jobs: [{ name: 'civic / collect', status: 'completed', conclusion: 'success', completed_at: run.updated_at }, { name: 'activities / collect', status: 'completed', conclusion: 'skipped' }] }
  const now = new Date('2026-10-14T12:00:00Z')
  assert.equal(health.feedHealth([observation], 'civic / collect', now).status, 'Job passed')
  assert.equal(health.feedHealth([observation], 'activities / collect', now).status, 'Skipped')
  assert.equal(health.feedHealth([{ run, jobs: null }], 'civic / collect', now).status, 'Unknown')
  assert.equal(health.feedHealth([observation], 'deals / collect', now).status, 'Unknown')
  assert.equal(health.feedHealth([observation], 'civic / collect', new Date('2026-10-15T12:00:00Z')).missed, true)
})
test('manual runs do not satisfy scheduled freshness and older successes remain visible', () => {
  const old = { run: { ...run, id: 2, created_at: '2026-10-13T06:00:00Z' }, jobs: [{ name: 'deals / collect', status: 'completed', conclusion: 'success', completed_at: '2026-10-13T07:00:00Z' }] }
  const latest = { run, jobs: [{ name: 'deals / collect', status: 'completed', conclusion: 'failure' }] }
  const state = health.feedHealth([{ run: { ...run, event: 'workflow_dispatch' }, jobs: old.jobs }, latest, old], 'deals / collect', new Date('2026-10-14T12:00:00Z'))
  assert.equal(state.status, 'Failed')
  assert.equal(state.lastSuccess, '2026-10-13T07:00:00Z')
  assert.equal(health.feedHealth([{ run: { ...run, event: 'workflow_dispatch' }, jobs: old.jobs }], 'deals / collect').missed, true)
})
test('the Supabase timer run is the slot evidence; a skipped late duplicate does not hide it', () => {
  const timer = { run: { ...run, id: 3, event: 'workflow_dispatch', conclusion: 'success', display_title: 'Dadspace workers timer slot 2026-10-23T07:17', created_at: '2026-10-23T06:18:00Z', updated_at: '2026-10-23T06:30:00Z' },
    jobs: [{ name: 'deals / collect', status: 'completed', conclusion: 'success', completed_at: '2026-10-23T06:30:00Z' }] }
  const lateDuplicate = { run: { ...run, id: 4, conclusion: 'success', created_at: '2026-10-23T11:40:00Z', updated_at: '2026-10-23T11:41:00Z' },
    jobs: [{ name: 'deals / collect', status: 'completed', conclusion: 'skipped' }] }
  const now = new Date('2026-10-23T12:00:00Z')
  assert.equal(health.isSlotRun(timer.run), true)
  assert.equal(health.isSlotRun({ ...timer.run, display_title: 'Dadspace workers' }), false, 'an ordinary manual run is not slot evidence')
  const state = health.feedHealth([lateDuplicate, timer], 'deals / collect', now)
  assert.equal(state.status, 'Job passed')
  assert.equal(state.lastSuccess, '2026-10-23T06:30:00Z')
  const slot = health.scheduledSlotHealth([lateDuplicate, timer], 'deals / collect', now)
  assert.equal(slot.delayMinutes, 1)
  assert.equal(slot.signal, 'Job passed; verify useful supply')
})

function dashboard(authResult, fetcher = async () => { throw new Error('should not fetch') }) {
  const client = { auth: { getUser: async () => authResult } }
  const session = load('lib/operations/session.ts', { 'server-only': {}, '@/lib/supabase/server': { createClient: async () => client }, './access': access }, { process: { env: { NEXT_PUBLIC_DADSPACE_SUPABASE_URL: 'https://example.supabase.co', NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY: 'public', DADSPACE_OPERATOR_USER_IDS: owner } } })
  return load('lib/operations/dashboard.ts', { 'server-only': {}, 'next/cache': { unstable_cache: fn => fn }, '@/lib/supabase/server': { createClient: async () => client }, './access': access, './session': session, './health': health },
    { process: { env: { NEXT_PUBLIC_DADSPACE_SUPABASE_URL: 'https://example.supabase.co', NEXT_PUBLIC_DADSPACE_SUPABASE_ANON_KEY: 'public', DADSPACE_OPERATOR_USER_IDS: owner } }, fetch: fetcher })
}
test('server gate rejects unauthenticated users and ignores user-editable admin claims before fetching', async () => {
  let calls = 0
  const fetcher = async () => { calls++; throw new Error('offline') }
  assert.equal((await dashboard({ data: { user: null }, error: null }, fetcher).getOperationsDashboard()).access, 'sign-in')
  assert.equal((await dashboard({ data: { user: { id: other, user_metadata: { admin: true }, app_metadata: { role: 'operator' } } }, error: null }, fetcher).getOperationsDashboard()).access, 'denied')
  assert.equal((await dashboard({ data: { user: ownerUser }, error: { message: 'expired' } }, fetcher).getOperationsDashboard()).access, 'sign-in')
  assert.equal(calls, 0)
})
test('authorised read shows unavailable evidence honestly and partial API failure does not drop other workers', async () => {
  const result = await dashboard({ data: { user: ownerUser }, error: null }).getOperationsDashboard()
  assert.equal(result.access, 'allowed')
  assert.equal(result.evidence.observations, null)
  let calls = 0
  const fetcher = async url => {
    calls++
    if (url.includes('original-content') || url.includes('shadow-review')) return { ok: false }
    if (url.includes('/jobs?')) return { ok: true, json: async () => ({ jobs: [{ name: 'news / news', status: 'completed', conclusion: 'success', completed_at: run.updated_at }], total_count: 1 }) }
    return { ok: true, json: async () => ({ workflow_runs: [run, { ...run, event: 'workflow_dispatch' }] }) }
  }
  const partial = await dashboard({ data: { user: ownerUser }, error: null }, fetcher).getOperationsDashboard()
  assert.equal(partial.evidence.observations.length, 1)
  assert.equal(partial.evidence.original, null)
  assert.equal(partial.evidence.shadow, null)
  assert.equal(calls, 4)
})

test('malformed public evidence fails safely after verified operator access', async () => {
  const result = await dashboard({ data: { user: ownerUser }, error: null }, async () => ({ ok: true, json: async () => null })).getOperationsDashboard()
  assert.equal(result.access, 'unavailable')
})

 test('only the confirmed owner can enter operations even with legacy allowlists', async () => {
  for (const user of [{ id: owner }, { ...ownerUser, email: 'other@example.com' }, { ...ownerUser, email_confirmed_at: undefined }, { ...ownerUser, is_anonymous: true }, { id: owner, user_metadata: { email: ownerUser.email } }]) {
    assert.equal((await dashboard({ data: { user }, error: null }).getOperationsDashboard()).access, 'denied')
  }
  assert.equal(access.isOperationsOwner({ ...ownerUser, email: 'IMRANSINVESTMENTS@gmail.com' }), true)
 })

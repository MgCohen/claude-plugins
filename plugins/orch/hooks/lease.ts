import { S, now, orch } from './state.ts'
import { isEnabled, log, readSession, writeHeartbeat, writeSession } from './backend.ts'

// The process that holds the lease: orch process prints the id and the start time of its parent, the claude process
// of this session. The supervisor releases a stale lease only when this process is gone (two writers, S0).
export async function findProcess($: any): Promise<void> {
  if (S.pid !== undefined) return
  try {
    const run = await orch($, ['process'], 15000)
    const value = run.ok ? JSON.parse(run.text) : undefined
    if (typeof value?.pid === 'number') {
      S.pid = value.pid
      S.started = String(value.started ?? '')
    } else await log($, `orch process failed: ${run.text.slice(0, 200)}`)
  } catch (error) {
    await log($, `orch process failed: ${String(error)}`)
  }
}

// A supervisor turn of this session runs: turn.json has no end, and the lease is supervisor or the turn started less
// than TURN_GRACE_MS ago (the claude -p process may not hold the lease yet). Then a live process must not take the lease
// and must not deliver: the supervisor turn has the same envelopes, and two writers split the transcript (S0).
export const TURN_GRACE_MS = 120000

export function supervisorTurnRuns(turn: any, lease: any, nowMs: number): boolean {
  if (!turn || typeof turn !== 'object' || turn.ended) return false
  if (lease?.holder === 'supervisor') return true
  const at = Date.parse(String(turn.at ?? ''))
  return Number.isFinite(at) && nowMs - at < TURN_GRACE_MS
}

export function mayTakeLease(holder: string, turn: any, lease: any, nowMs: number): boolean {
  return holder !== 'live' || !supervisorTurnRuns(turn, lease, nowMs)
}

export function mayDeliver(holder: string, turn: any, lease: any, nowMs: number): boolean {
  return lease?.holder === holder && mayTakeLease(holder, turn, lease, nowMs)
}

export async function turnOpen($: any): Promise<{ turn: any; lease: any; now: number }> {
  return { turn: await readSession($, 'turn.json'), lease: await readSession($, 'lease.json'), now: await $.clock.now() }
}

export async function writeLease($: any, holder: string, reason: unknown): Promise<void> {
  if (!S.dir) return
  const lease: Record<string, unknown> = { holder, since: await now($), reason }
  if (holder !== 'none' && S.pid !== undefined) {
    lease.pid = S.pid
    lease.started = S.started
  }
  await writeSession($, 'lease.json', lease)
}

export async function beat($: any): Promise<void> {
  if (!S.dir) return
  if (!(await isEnabled($))) {
    await writeLease($, 'none', { event: 'archived' })
    await log($, 'the enabled file is gone: lease released, plugin inactive')
    S.dir = undefined
    return
  }
  await writeHeartbeat($)
  const lease = await readSession($, 'lease.json')
  if (lease?.holder === S.holder) return
  if (lease?.holder === 'none') {
    if (!mayTakeLease(S.holder, await readSession($, 'turn.json'), lease, await $.clock.now())) return
    await writeLease($, S.holder, { event: 'lease taken back', was: lease })
    await log($, 'lease taken back')
    return
  }
  await log($, `lease conflict: the store says ${lease?.holder}, this process is ${S.holder}`)
}

export async function releaseLease($: any, e: unknown): Promise<void> {
  if (!S.dir) return
  const lease = await readSession($, 'lease.json')
  if (lease?.holder === S.holder) await writeLease($, 'none', { event: 'session.end', end: e })
  await log($, `session.end ${JSON.stringify(e)}`)
}

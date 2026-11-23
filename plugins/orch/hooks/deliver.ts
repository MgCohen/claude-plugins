// The session deliverer: a reactor of the live session on the stream.
// A child `orch watch --to session:<id>` pushes one JSON line for each new envelope. When the session is idle,
// the deliverer lists the envelopes with no ack (with their texts), submits them as one turn, and posts an ack for each.
import { S, orch } from './state.ts'
import { controlState, log } from './backend.ts'
import { ack, post, type Envelope } from './stream.ts'
import { mayDeliver, turnOpen } from './lease.ts'

export const SEPARATOR = '\n\n---\n\n'

function parseLines(text: string): Envelope[] {
  return text
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(line => line.startsWith('{'))
    .map(line => JSON.parse(line) as Envelope)
}

// The push: a child process for the life of the module. Leaving the loop kills it; the beat starts it again.
export async function watchLoop($: any): Promise<void> {
  if (S.watching || !S.dir || !S.id || S.holder !== 'live') return
  S.watching = true
  let buffer = ''
  try {
    const child = $.process.spawn({ argv: ['orch', 'watch', '--to', `session:${S.id}`] })
    await log($, 'watch started')
    for await (const piece of child) {
      if (piece?.stream !== 'stdout' || typeof piece.text !== 'string') continue
      buffer += piece.text
      const end = buffer.lastIndexOf('\n')
      if (end < 0) continue
      const lines = parseLines(buffer.slice(0, end))
      buffer = buffer.slice(end + 1)
      if (lines.some(line => !S.handled.has(line.id))) {
        S.wanted = true
        await deliver($)
      }
    }
    await log($, 'watch ended')
  } catch (error) {
    await log($, `watch failed: ${String(error)}`)
  } finally {
    S.watching = false
  }
}

async function submit($: any, text: string): Promise<boolean> {
  const result = await $.prompt.submit({ text })
  if (result && typeof result.drop === 'string') {
    if (S.dropped !== result.drop) {
      await log($, `submit dropped, will try again: ${result.drop}`)
      await post($, 'blocked', `session:${S.id}`, 'user', { text: `delivery blocked: ${result.drop}`, reason: result.drop })
    }
    S.dropped = result.drop
    return false
  }
  if (S.dropped !== '') {
    await post($, 'blocked', `session:${S.id}`, 'user', { text: 'delivery unblocked', reason: null })
  }
  S.dropped = ''
  return true
}

// Delivers the envelopes with no ack as one turn. It asks the stream for the list, so an envelope that the
// ask_user tool, the chat or a supervisor turn acknowledged is never delivered two times.
export async function deliver($: any): Promise<void> {
  if (!S.dir || !S.id || S.busy || !S.idle || !S.wanted || S.holder !== 'live') return
  S.busy = true
  try {
    // A stopped session keeps its inbox: no delivery until orch resume.
    if ((await controlState($)) !== 'active') return
    // A supervisor turn has these envelopes until its end: no second delivery, no second writer.
    const open = await turnOpen($)
    if (!mayDeliver(S.holder, open.turn, open.lease, open.now)) return
    const run = await orch($, ['watch', '--to', `session:${S.id}`, '--list'])
    if (!run.ok) {
      await log($, `list failed: ${run.text.slice(0, 200)}`)
      return
    }
    const items = parseLines(run.text).filter(item => !S.handled.has(item.id))
    if (items.length === 0) {
      S.wanted = false
      return
    }
    if (!S.idle) return
    S.inputFrom = [...new Set(items.map(item => item.from))].join(',')
    if (!(await submit($, items.map(item => item.text ?? item.subject ?? '').join(SEPARATOR)))) return
    for (const item of items) await ack($, item, 'live')
    // A question that reached the session as an envelope is shown: the recurring check does not show it again.
    for (const item of items) if (item.kind === 'question') S.shown.add(item.thread ?? item.id)
    S.wanted = false
    await log($, `delivered ${items.map(item => `${item.kind} ${item.id}`).join(', ')}`)
  } catch (error) {
    await log($, `deliver failed: ${String(error)}`)
  } finally {
    S.busy = false
  }
}

// The beat: start the watch again if it ended, and try a delivery that the stop latch refused.
export async function tick($: any): Promise<void> {
  if (!S.dir || S.holder !== 'live') return
  if (!S.watching) watchLoop($).catch((error: unknown) => log($, `watch failed: ${String(error)}`))
  if (S.wanted && (S.dropped !== '' || !S.busy)) await deliver($)
}

// The trace of the session (session.input, session.output, session.tool), posted to the stream.
import { S, now } from './state.ts'
import { readSession, writeSession } from './backend.ts'
import { post } from './stream.ts'

export async function emit($: any, kind: string, from: string, to: string, data: Record<string, unknown>, refs: Record<string, unknown> = {}): Promise<string> {
  return post($, kind, from, to, data, { refs })
}

export function blocksOf(message: any): any[] {
  const content = message?.content ?? message?.message?.content
  if (typeof content === 'string') return [{ type: 'text', text: content }]
  return Array.isArray(content) ? content : []
}

export function textOf(message: any): string {
  return blocksOf(message)
    .filter((block: any) => block.type === 'text' && typeof block.text === 'string')
    .map((block: any) => block.text)
    .join(' ')
    .trim()
}

export function rowText(message: any): string {
  const parts = blocksOf(message).map((block: any) =>
    block.type === 'text' ? block.text : block.type === 'tool_result' ? '[tool result]' : '',
  )
  return parts.filter((text: string) => text !== '').join(' ')
}

export async function inputSender($: any, origin: string): Promise<{ from: string; turnStart?: string }> {
  if (S.holder !== 'supervisor' || !S.dir) {
    if (origin === 'plugin' && S.inputFrom !== '') return { from: S.inputFrom }
    return { from: origin === 'composer' ? 'user' : origin }
  }
  const turn = await readSession($, 'turn.json')
  return typeof turn?.from === 'string' ? { from: turn.from, turnStart: turn.event } : { from: 'supervisor' }
}

export async function emitRow($: any, e: any): Promise<void> {
  if (e.door === 'prompt') {
    const origin = String(e.origin?.kind ?? 'unknown')
    const sender = await inputSender($, origin)
    const refs: Record<string, unknown> = { row: e.uuid }
    if (sender.turnStart) refs.turnStart = sender.turnStart
    await emit($, 'session.input', sender.from, `session:${S.id}`, { text: rowText(e.message), origin }, refs)
    return
  }
  if (e.door !== 'response') return
  const to = S.holder === 'live' ? 'user' : 'supervisor'
  for (const block of blocksOf(e.message)) {
    if (block.type !== 'tool_use') continue
    const input = JSON.stringify(block.input ?? {}).slice(0, 2000)
    await emit($, 'session.tool', `session:${S.id}`, to, { text: String(block.name), name: block.name, input }, { row: e.uuid, tool: block.id })
  }
  const text = textOf(e.message)
  if (text === '') return
  const id = await emit($, 'session.output', `session:${S.id}`, to, { text }, { row: e.uuid })
  await writeSession($, 'last-output.json', { event: id, at: await now($) })
}

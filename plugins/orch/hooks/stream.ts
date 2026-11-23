// The TypeScript binding of the Stream API: post, ack and nudge. The C# binding (EventStream.cs) is the reference.
// Only C# renders: the plugin gets the text for the model from orch watch or orch read --for.
import { S, newId } from './state.ts'
import { bodyPath, createEnvelope, readSession, readTemplate } from './backend.ts'

export type Envelope = { id: string; kind: string; from: string; to: string; stream?: string; thread?: string; needs?: string; subject?: string; refs?: Record<string, unknown>; text?: string }

export type PostOptions = { thread?: string; needs?: string; refs?: Record<string, unknown> }

const META: Record<string, any> = {}

// The kinds that the plugin may post. A message kind needs its templates/<kind>/meta.json.
export const MESSAGE_KINDS = ['brief', 'message', 'question', 'plan', 'answer', 'review', 'report', 'update', 'notice', 'ack']
export const TRACE_KINDS = ['session.input', 'session.output', 'session.tool', 'blocked', 'meta.update']

export function knownKind(kind: string): boolean {
  return MESSAGE_KINDS.includes(kind) || TRACE_KINDS.includes(kind)
}

// The one subject rule. Subjects.Of in Event.cs has the same rule, and the contract tests check both.
export function subject(kind: string, data: Record<string, unknown>): string {
  let text: string
  if (kind === 'answer' && data.text !== undefined) text = String(data.text ?? '')
  else if (kind === 'review' && data.verdict !== undefined) text = `${data.verdict}${typeof data.text === 'string' && data.text.length > 0 ? `: ${data.text}` : ''}`
  else if (kind === 'ack' && data.state !== undefined) text = `${data.state} (${data.by ?? ''})`
  else if (kind === 'notice' && data.kind !== undefined) text = `${data.kind}${typeof data.question === 'string' && data.question.length > 0 ? `: ${data.question}` : ''}`
  else text = String(data.question ?? data.summary ?? data.title ?? data.text ?? '')
  // One line: the first sentence, cut at 80 characters (D9). A sentence ends with . ! or ? and a space.
  const line = text.replace(/\s+/g, ' ').trim()
  const end = line.search(/[.!?](?= )/)
  return (end >= 0 ? line.slice(0, end + 1) : line).slice(0, 80)
}

export function classOf(party: string): string {
  return party.startsWith('session:') ? 'session' : party
}

async function meta($: any, kind: string): Promise<any> {
  if (META[kind] !== undefined) return META[kind]
  const value = (await readTemplate($, kind, 'meta')) ?? null
  const schema = (await readTemplate($, kind, 'schema')) ?? null
  META[kind] = value === null ? null : { ...value, required: schema?.required ?? [], dependentRequired: schema?.dependentRequired ?? {} }
  return META[kind]
}

function allows(list: string[], party: string): boolean {
  return list.includes('*') || list.includes(classOf(party))
}

// Level 2 and 3 of the type check: a known type, the required and dependentRequired fields of schema.json, and the from and to of meta.json.
// The engine checks the full schema before the tool call (level 1).
// The plugin posts no reply and no answer, so the reply-type and the first-answer checks stay in C#: an answer and a
// review always go through orch (orch answer, orch chat-answer, orch review).
async function check($: any, kind: string, from: string, to: string, body: Record<string, unknown>): Promise<void> {
  if (!knownKind(kind)) throw new Error(`${kind}: unknown kind. Known: ${[...MESSAGE_KINDS, ...TRACE_KINDS].join(', ')}`)
  if (!MESSAGE_KINDS.includes(kind)) return
  if (kind === 'answer' || kind === 'review') throw new Error(`${kind}: post it with orch, which checks the reply type and the first answer`)
  const m = await meta($, kind)
  if (m === null) throw new Error(`${kind}: no templates/${kind}/meta.json`)
  const missing = (m.required as string[]).filter(field => body[field] === undefined || body[field] === null)
  if (missing.length > 0) throw new Error(`${kind}: missing fields ${missing.join(', ')}`)
  for (const [field, needed] of Object.entries(m.dependentRequired as Record<string, string[]>)) {
    if (body[field] === undefined) continue
    const absent = needed.filter(other => body[other] === undefined || body[other] === null)
    if (absent.length > 0) throw new Error(`${kind}: ${field} needs the fields ${absent.join(', ')}`)
  }
  if (!allows(m.from, from)) throw new Error(`${kind}: from ${from} is not allowed. Allowed: ${m.from.join(', ')}`)
  if (!allows(m.to, to)) throw new Error(`${kind}: to ${to} is not allowed. Allowed: ${m.to.join(', ')}`)
}

function clean(data: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(data)) if (value !== undefined && value !== null) out[key] = value
  return out
}

// The work stream of this session: the stream field of its registry entry (session.json). The C# rule is EventStream.StreamOf.
export async function streamOf($: any): Promise<string | undefined> {
  if (!S.dir) return undefined
  const entry = await readSession($, 'session.json')
  return typeof entry?.stream === 'string' && entry.stream.length > 0 ? entry.stream : undefined
}

// Post: the body first, then the envelope. The envelope is the commit point.
export async function post($: any, kind: string, from: string, to: string, data: Record<string, unknown>, options: PostOptions = {}): Promise<string> {
  if (!S.store) return ''
  const body = clean(data)
  await check($, kind, from, to, body)
  let ms = await $.clock.now()
  if (ms <= S.lastMs) ms = S.lastMs + 1
  S.lastMs = ms
  const at = new Date(await $.clock.now()).toISOString()
  const day = new Date(ms).toISOString().slice(0, 10)
  const id = `${ms}-${newId().slice(0, 8)}-${S.holder}`
  const path = bodyPath(day, id)
  const envelope: Record<string, unknown> = { id, at, session: S.id, kind, from, to, subject: subject(kind, body), body: path, refs: clean(options.refs ?? {}) }
  if (options.thread) envelope.thread = options.thread
  if (options.needs) envelope.needs = options.needs
  const stream = await streamOf($)
  if (stream) envelope.stream = stream
  await createEnvelope($, day, id, body, envelope)
  return id
}

// The pong: an ack with refs.of, from this session to the sender.
export async function ack($: any, envelope: Envelope, by: string): Promise<string> {
  S.handled.add(envelope.id)
  return post($, 'ack', `session:${S.id}`, envelope.from, { state: 'delivered', by }, { thread: envelope.thread, refs: { of: envelope.id } })
}

// A peer nudge to another session: a ping with no content. The receiver consumes it in session.receive.
export const NUDGE = '[orch nudge] look at the stream'

export async function nudgePeer($: any, to: string): Promise<void> {
  if (!to.startsWith('session:')) return
  await $.session.send({ to: { sessionId: to.slice('session:'.length) }, text: NUDGE })
}

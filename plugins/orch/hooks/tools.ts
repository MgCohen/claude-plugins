// The orch tools: one tool for each message type. Each tool posts to the stream; the tool input schema is the template schema.
import { MAX_WAIT_SECONDS, S, orch } from './state.ts'
import { log, readPolicy, readSession, readTemplate } from './backend.ts'
import { ack, nudgePeer, post, type Envelope } from './stream.ts'

export const ASK_TOOL = 'mcp__orch__ask_user'
export const REPORT_TOOL = 'mcp__orch__report'
export const UPDATE_TOOL = 'mcp__orch__update'
export const SPAWN_TOOL = 'mcp__orch__spawn_child'
export const ANSWER_TOOL = 'mcp__orch__answer'
export const QUESTIONS_TOOL = 'mcp__orch__questions'
export const SEND_TOOL = 'mcp__orch__send'
export const PLAN_TOOL = 'mcp__orch__plan'

async function templateSchema($: any, kind: string): Promise<any> {
  const schema = await readTemplate($, kind, 'schema')
  if (!schema?.properties) throw new Error(`orch: no schema for template ${kind}`)
  return { type: 'object', properties: { ...schema.properties }, required: schema.required ?? [] }
}

async function purpose($: any, kind: string): Promise<string> {
  const meta = await readTemplate($, kind, 'meta')
  return typeof meta?.purpose === 'string' ? `Use it when: ${meta.purpose}` : ''
}

async function riskLevels($: any): Promise<{ names: string[]; text: string }> {
  const policy = await readPolicy($)
  const levels: any[] = Array.isArray(policy?.levels) && policy.levels.length > 0 ? policy.levels : [{ name: 'low' }, { name: 'medium' }, { name: 'high' }]
  const text = levels.map(level => `${level.name}: ${level.description ?? ''}`).join(' ')
  return { names: levels.map(level => String(level.name)), text }
}

export async function registerTools($: any): Promise<void> {
  const risk = await riskLevels($)
  const question = await templateSchema($, 'question')
  question.properties.risk = { ...question.properties.risk, enum: risk.names, description: `Pick the level that fits. Required with a defaultOption. ${risk.text}` }
  await $.tool.register({
    name: 'ask_user',
    description: `${await purpose($, 'question')} Put one question in the user queue (the question template). The skill orch:orch-ask tells how to fill it. Only question is required. For a choice, give options, a recommendation, a risk and a defaultOption: if no answer comes in time, the orchestrator can apply the default, by the risk level. For facts, give only the question and the context: there is no default. The user answers in free text. With waitSeconds 0 it returns PENDING at once: end your turn, and the answer arrives later as a new message that starts with "Answer to question". With waitSeconds more than 0 it blocks up to that time (580 maximum) and returns ANSWER: <text>, or PENDING when no answer came.`,
    inputSchema: question,
    isDeferred: false,
  })
  await $.tool.register({
    name: 'plan',
    description: `${await purpose($, 'plan')} The user approves, changes or refuses the plan. It returns at once: end your turn, and the verdict arrives later as a new message that starts with "Review of plan".`,
    inputSchema: await templateSchema($, 'plan'),
    isDeferred: false,
  })
  await $.tool.register({
    name: 'report',
    description: `${await purpose($, 'report')} Tell your parent or the user that the work is done or blocked (the report template). The reader must act. The skill orch:orch-report tells when to report and when to update.`,
    inputSchema: await templateSchema($, 'report'),
    isDeferred: false,
  })
  await $.tool.register({
    name: 'update',
    description: `${await purpose($, 'update')} Show your progress (the update template). Nobody must act on it: the UI shows it in the session tree.`,
    inputSchema: await templateSchema($, 'update'),
    isDeferred: false,
  })
  const message = await templateSchema($, 'message')
  message.properties.to = { type: 'string', description: 'The receiver: "parent", "user", or a session id (the first characters are enough).' }
  message.required = ['to', 'text']
  await $.tool.register({
    name: 'send',
    description: `${await purpose($, 'message')} The receiver gets the text as a new message that starts with "Message from".`,
    inputSchema: message,
    isDeferred: false,
  })
  await $.tool.register({
    name: 'answer',
    description:
      'Answer an open question of a child for the user (a question that arrived as "Question from child"). Use only the words of the user, never your own choice. The child gets the answer as a new message.',
    inputSchema: {
      type: 'object',
      properties: {
        question: { type: 'string', description: 'The id of the question.' },
        decision: { type: 'string', description: 'Old name of question. It stays valid.' },
        text: { type: 'string', description: 'The answer of the user, in the words of the user.' },
      },
      required: ['text'],
    },
    isDeferred: false,
  })
  await $.tool.register({
    name: 'questions',
    description: 'List all open questions in the orchestrator queue: question id, risk, default, session and question. Use it when the user asks which questions are open.',
    inputSchema: { type: 'object', properties: {} },
    isDeferred: false,
  })
  const brief = await templateSchema($, 'brief')
  delete brief.properties.parent
  delete brief.properties.allowDefaults
  brief.properties.inApp = {
    type: 'boolean',
    description: 'Default true: if this session runs in the desktop app, start the child in the app, with Remote Control. false: the supervisor starts the child, opens it in the app and turns its Remote Control on. Use false in a turn that came from Remote Control (the phone or claude.ai): the app refuses start_session there.',
  }
  await $.tool.register({
    name: 'spawn_child',
    description: `${await purpose($, 'brief')} Start a child session under the orchestrator (the brief template). The skill orch:orch-brief tells how to fill it. This is the only way to start a child: never use core:spawn or a start_session call of your own. When the child reports done or blocked, you get a new message that starts with "Report from child".`,
    inputSchema: brief,
    isDeferred: false,
  })
}

function self(): string {
  return `session:${S.id}`
}

async function parentId($: any): Promise<string | undefined> {
  const entry = await readSession($, 'session.json')
  return typeof entry?.parent === 'string' ? entry.parent : undefined
}

/**
 * The output of `orch decisions` (also named `orch questions`) with no open question. The old text
 * "No open decisions." of an older `orch` also counts (C3-F4).
 */
export const NO_OPEN_QUESTIONS = /^No open (questions|decisions)\b/

export const EARLY_DONE =
  'orch: the report was not recorded. This session has an open question, so the work is not done. The end of a step is an update: call mcp__orch__update. Report done after the answer arrives.'

export async function report($: any, e: any): Promise<any> {
  if (!S.dir) return { deny: 'orch: this session is not enabled' }
  if (e.state === 'done' && S.id) {
    const open = await orch($, ['decisions', '--session', S.id])
    if (open.ok && !NO_OPEN_QUESTIONS.test(open.text)) return { result: EARLY_DONE }
  }
  const fields = { state: e.state, summary: e.summary, done: e.done, next: e.next, blockers: e.blockers, links: e.links, details: e.details }
  const needs = e.state === 'done' || e.state === 'blocked' ? 'ack' : undefined
  await post($, 'report', self(), 'user', fields, { needs })
  return { result: 'Recorded.' }
}

export async function update($: any, e: any): Promise<any> {
  if (!S.dir) return { deny: 'orch: this session is not enabled' }
  await post($, 'update', self(), 'user', { step: e.step, progress: e.progress, summary: e.summary })
  return { result: 'Recorded.' }
}

export async function send($: any, e: any): Promise<any> {
  if (!S.dir) return { deny: 'orch: this session is not enabled' }
  let to = String(e.to ?? '')
  if (to === 'parent') {
    const parent = await parentId($)
    if (!parent) return { result: 'orch: this session has no parent. Send to "user" or to a session id.' }
    to = `session:${parent}`
  }
  if (to === 'user' || to.startsWith('session:') && to.length > 40) {
    await post($, 'message', self(), to, { text: e.text })
    await nudgePeer($, to).catch((error: unknown) => log($, `peer nudge failed: ${String(error)}`))
  } else {
    const run = await orch($, ['post', 'message', '--to', to, '--from', self(), '--text', String(e.text)])
    if (!run.ok) return { result: `orch: the message was not sent: ${run.text.slice(0, 400)}` }
  }
  return { result: `Sent to ${to}.` }
}

export async function plan($: any, e: any): Promise<any> {
  if (!S.dir) return { deny: 'orch: this session is not enabled' }
  const id = String(e.tool_use_id)
  await post($, 'plan', self(), 'user', { title: e.title, steps: e.steps, context: e.context }, { thread: id, needs: 'review' })
  await log($, `plan ${id} posted`)
  return { result: `PENDING: Plan ${id} waits for the review of the user. Show the plan in your reply text, then end your turn. The verdict arrives as a new message that starts with "Review of plan ${id}".` }
}

export async function spawnChild($: any, e: any): Promise<any> {
  if (!S.dir || !S.id) return { deny: 'orch: this session is not enabled' }
  const argv = ['new', '--title', String(e.title), '--goal', String(e.goal), '--parent', S.id, '--created-by', 'spawn_child', '--cwd', String(e.cwd ?? S.cwd)]
  if (e.scope) argv.push('--scope', String(e.scope))
  if (e.doneWhen) argv.push('--done-when', String(e.doneWhen))
  if (Array.isArray(e.skills) && e.skills.length > 0) argv.push('--skills', e.skills.join(','))
  if (e.agent) argv.push('--agent', String(e.agent))
  if (e.type) argv.push('--type', String(e.type))
  if (e.stream) argv.push('--stream', String(e.stream))
  if (e.workflow) argv.push('--workflow', String(e.workflow))
  if (e.worktree === true) argv.push('--worktree')
  if (e.background === true) argv.push('--background')
  if (e.where === 'cloud') argv.push('--where', 'cloud')
  if (e.inApp !== false) argv.push('--app-start')
  const run = await orch($, argv)
  if (!run.ok) {
    await log($, `spawn_child failed: ${run.text.slice(0, 400)}`)
    return { result: `orch: spawn_child failed: ${run.text.slice(0, 400)}. Fix the fields, or do the work yourself.` }
  }
  const start = appStart(run.text)
  if (start) {
    await log($, `spawn_child ${e.title}: app start ${start.file}`)
    return { result: start.instruction }
  }
  const child = run.text.split(/\r?\n/).pop() ?? run.text
  await log($, `spawn_child ${child} ${e.title}`)
  return { result: `Started child "${e.title}" (${child}). It reports back as a new message that starts with "Report from child". If you have nothing else to do now, end your turn.` }
}

// The output of `orch new --app-start` for a parent in the desktop app: the line "app-start <file>", then the app call
// that starts the child (R-F8). Any other output is the id of a child that the supervisor starts.
export const APP_START_MARK = 'app-start '

export function appStart(output: string): { file: string; instruction: string } | undefined {
  const lines = output.trim().split(/\r?\n/)
  const first = lines.findIndex(line => line.startsWith(APP_START_MARK))
  if (first < 0) return undefined
  return { file: lines[first].slice(APP_START_MARK.length).trim(), instruction: lines.slice(first + 1).join('\n').trim() }
}

export async function answerChild($: any, e: any): Promise<any> {
  if (!S.dir) return { deny: 'orch: this session is not enabled' }
  // The input field question is the new name; decision is the old name, kept for live sessions (C2).
  const id = e.question ?? e.decision
  if (!id) return { result: 'orch: give the question id in the field question.' }
  const run = await orch($, ['answer', String(id), String(e.text), '--via', self()])
  await log($, `answer ${id}: ${run.text.slice(0, 200)}`)
  return { result: run.ok ? `${run.text} The child gets the answer as a new message.` : `orch: the answer was not recorded: ${run.text.slice(0, 400)}` }
}

export async function listQuestions($: any): Promise<any> {
  if (!S.dir) return { deny: 'orch: this session is not enabled' }
  const run = await orch($, ['decisions'])
  return { result: run.ok ? run.text : `orch: the list failed: ${run.text.slice(0, 400)}` }
}

function promptText(message: any): string {
  const content = message?.content
  if (typeof content === 'string') return content
  if (!Array.isArray(content)) return ''
  return content.filter((part: any) => part?.type === 'text').map((part: any) => String(part.text ?? '')).join('\n').trim()
}

const REMINDER = /<system-reminder>[\s\S]*?<\/system-reminder>/gi
const ANSWER_PREFIX = /^answer:/i

// A chat message is an answer only when it starts with "answer:". Questions and requests in the chat
// must not close a question. App reminder blocks are not text of the user, so they go first.
export function chatAnswer(text: string): string | undefined {
  const clean = text.replace(REMINDER, '').trim()
  if (!ANSWER_PREFIX.test(clean)) return undefined
  const answer = clean.replace(ANSWER_PREFIX, '').trim()
  return answer === '' ? undefined : answer
}

// A chat message that starts with "answer:" answers the open question of this session, only when exactly one is open.
// orch chat-answer posts the answer with via chat and its ack, so the deliverer does not send it again.
export async function answerFromChat($: any, e: any): Promise<void> {
  if (!S.dir || !S.id || e.origin?.kind !== 'composer') return
  const text = chatAnswer(promptText(e.message))
  if (text === undefined) return
  const run = await orch($, ['chat-answer', S.id, text])
  await log($, `chat answer: ${run.text.slice(0, 200)}`)
}

export async function askUser($: any, e: any): Promise<any> {
  if (!S.dir) return { deny: 'orch: this session is not enabled' }
  const id = String(e.tool_use_id)
  const wait = Math.max(0, Math.min(MAX_WAIT_SECONDS, Number(e.waitSeconds ?? 0)))
  const fields = { question: e.question, context: e.context, snippet: e.snippet, options: e.options, recommendation: e.recommendation, risk: e.risk, defaultOption: e.defaultOption, waitSeconds: wait }
  try {
    await post($, 'question', self(), 'user', fields, { thread: id, needs: 'answer' })
  } catch (error) {
    return { result: `orch: the question was not recorded: ${error instanceof Error ? error.message : String(error)}. Fix the fields and call the tool again.` }
  }
  const later = `Question ${id} is in the user queue. If you have a parent session, it sees the question too. Write the question in your reply text with the "Question" template of the skill orch:orch-reply, so that the user can read it here. Tell the user: "In the chat, start the answer with \`answer:\`." A chat message without \`answer:\` does not close the question. The user can also answer in the parent session. End your turn now. A chat message that starts with \`answer:\` is your answer. An answer from elsewhere arrives as a new message that starts with "Answer to question ${id}".`
  if (wait === 0) {
    await log($, `ask_user ${id} pending`)
    return { result: `PENDING: ${later}` }
  }
  await log($, `ask_user ${id} waiting ${wait}s`)
  const run = await orch($, ['watch', '--to', self(), '--kind', 'answer', '--thread', id, '--once', '--timeout', String(wait), '--render', 'tool'], Math.min(600000, (wait + 15) * 1000))
  const line = run.ok ? run.text.split(/\r?\n/).find(text => text.trim().startsWith('{')) : undefined
  if (!line) {
    await log($, `ask_user ${id} timed out, now pending`)
    return { result: `PENDING: no answer in ${wait}s. ${later}` }
  }
  const answer = JSON.parse(line) as Envelope
  await ack($, answer, 'tool-result')
  await log($, `ask_user ${id} answered`)
  return { result: answer.text ?? `ANSWER: ${answer.subject ?? ''}` }
}

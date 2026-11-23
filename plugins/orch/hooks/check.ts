// The recurring check of a root orchestrator session (P1-F12): about every 5 minutes, with no request of the user.
// It reads the open questions and the envelopes with no ack. A question that the root did not show yet becomes one turn
// that tells the root to show it to the user. An envelope with no ack (for example a child report) goes to the deliverer.
import { S, orch } from './state.ts'
import { log } from './backend.ts'
import { deliver } from './deliver.ts'

export const CHECK_MS = 300000

// A question line of `orch decisions`: "<id> [<risk>] <session title>: <question>". Option lines start with spaces.
export function questionLines(text: string): { id: string; line: string }[] {
  return text
    .split(/\r?\n/)
    .filter(line => /^\S+ \[[a-z]+\] /.test(line))
    .map(line => ({ id: line.split(' ')[0], line }))
}

export function checkPrompt(lines: string[]): string {
  return [
    `Recurring check of the orchestrator: ${lines.length} open question(s) that you did not show to the user yet.`,
    ...lines.map(line => `- ${line}`),
    'Show each one to the user now with the "Question" template of orch:orch-reply. Then end your turn.',
  ].join('\n')
}

export async function rootCheck($: any): Promise<void> {
  if (!S.root || !S.dir || !S.id || S.holder !== 'live' || S.busy || !S.idle) return
  try {
    const pending = await orch($, ['watch', '--to', `session:${S.id}`, '--list'])
    if (pending.ok && pending.text.trim() !== '') {
      S.wanted = true
      await deliver($)
      return
    }
    const run = await orch($, ['decisions'])
    if (!run.ok) return
    const open = questionLines(run.text)
    const fresh = open.filter(q => !S.shown.has(q.id))
    if (fresh.length === 0) return
    const result = await $.prompt.submit({ text: checkPrompt(fresh.map(q => q.line)) })
    if (result && typeof result.drop === 'string') {
      await log($, `root check dropped: ${result.drop}`)
      return
    }
    for (const q of fresh) S.shown.add(q.id)
    await log($, `root check: ${fresh.length} question(s) shown`)
  } catch (error) {
    await log($, `root check failed: ${String(error)}`)
  }
}

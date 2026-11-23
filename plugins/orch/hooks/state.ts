export const TICK_MS = 3000
export const MAX_WAIT_SECONDS = 580
export const ROW_CHARS = 4000

export const S: {
  id?: string
  alias?: string
  aliasTried?: boolean
  root?: boolean
  shown: Set<string>
  dir?: string
  store?: string
  home: string
  cwd?: string
  holder: string
  busy: boolean
  idle: boolean
  dropped: string
  timers?: boolean
  watching: boolean
  wanted: boolean
  handled: Set<string>
  inputFrom: string
  lastMs: number
  pid?: number
  started?: string
} = {
  dropped: '',
  holder: 'live',
  home: '',
  busy: false,
  idle: true,
  watching: false,
  wanted: false,
  handled: new Set<string>(),
  shown: new Set<string>(),
  inputFrom: '',
  lastMs: 0,
}

export async function now($: any): Promise<string> {
  return new Date(await $.clock.now()).toISOString()
}

export function newId(): string {
  const hex = Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16))
  hex[12] = '4'
  hex[16] = '89ab'.charAt(Math.floor(Math.random() * 4))
  const h = hex.join('')
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`
}

// The home folder (templates, config): ORCH_HOME, else the answer of `orch home`, else the plugin folder, where the
// marketplace copy carries templates/ (tools/publish-plugin.ps1). The plugin keeps no path of its own, so a copy in a
// marketplace works on each computer that has `orch`, also with an `orch` older than `orch home` (P1-F2).
export async function homeRoot($: any): Promise<string> {
  const env = await $.env.get('ORCH_HOME')
  if (env) return env
  if (S.home) return S.home
  const run = await orch($, ['home'], 15000)
  const line = run.ok ? run.text.split(/\r?\n/).pop()?.trim() : undefined
  S.home = line || $.plugin.root
  return S.home
}

export async function orch($: any, argv: string[], timeoutMs = 60000): Promise<{ ok: boolean; text: string; code: number }> {
  const run = await $.process.run(['orch', ...argv], { timeoutMs })
  const text = String(run.exitCode === 0 ? run.stdout ?? '' : run.stderr || run.stdout || '').trim()
  return { ok: run.exitCode === 0, text, code: run.exitCode }
}

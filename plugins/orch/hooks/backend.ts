// The store backend of the plugin hooks: the only hook module with store IO ($.fs).
// Version 1 and version 2 both use local files here: a hook has a 10 s budget, so the plugin never calls Notion.
// The other modules name an entity (a session file, an envelope, a template), and this module knows the paths.
import { S, now } from './state.ts'

// The files in the folder of one session.
export type SessionFile = 'lease.json' | 'turn.json' | 'status.json' | 'session.json' | 'last-output.json'

export type TemplateFile = 'meta' | 'schema'

// A write that breaks a store rule: a second create of an id, or a save of an old version.
export class StoreConflict extends Error {}

async function readText($: any, path: string): Promise<string | undefined> {
  return (await $.fs.exists(path)) ? String(await $.fs.read(path)) : undefined
}

async function readJson($: any, path: string): Promise<any> {
  const text = await readText($, path)
  if (text === undefined) return undefined
  try {
    return JSON.parse(text)
  } catch {
    return { text }
  }
}

function json(value: unknown): string {
  return JSON.stringify(value, null, 2)
}

// Rule 1: a create of an id that exists fails (claims, first answer).
async function create($: any, path: string, text: string): Promise<void> {
  if (await $.fs.exists(path)) throw new StoreConflict(`${path}: the id exists`)
  await $.fs.write(path, text)
}

// The version of a stored file: a 64-bit FNV-1a hash of its UTF-8 text, as a signed 64-bit number. Never 0, because
// 0 means "not stored". The C# side uses the same rule (Versions.Of in Orchestrator.Store/Local), so both sides agree.
export function versionOf(text: string | undefined): bigint {
  if (text === undefined) return 0n
  let hash = 0xcbf29ce484222325n
  for (const b of new TextEncoder().encode(text)) {
    hash ^= BigInt(b)
    hash = (hash * 0x100000001b3n) & 0xffffffffffffffffn
  }
  return hash === 0n ? 1n : BigInt.asIntN(64, hash)
}

// Rule 2: a save with an expected version fails if the file on disk has another version (another text). With no
// expected version, the save replaces the file. A caller passes the version that it read (readSessionVersioned).
async function replace($: any, path: string, value: unknown, expected?: bigint): Promise<void> {
  if (expected !== undefined) {
    const version = versionOf(await readText($, path))
    if (version !== expected) throw new StoreConflict(`${path}: version ${expected} is old, the store has ${version}`)
  }
  await $.fs.write(path, json(value))
}

// The store root: ORCH_STORE, else the default store root of H1, %LOCALAPPDATA%\orch\store. C# (Home.DefaultStoreRoot)
// and install.ps1 -Store use the same default. With no LOCALAPPDATA (not Windows): $HOME/.local/share/orch/store, as .NET.
export async function storeRoot($: any): Promise<string> {
  const store = await $.env.get('ORCH_STORE')
  if (store) return store
  const local = await $.env.get('LOCALAPPDATA')
  if (local) return `${local.replace(/\\/g, '/')}/orch/store`
  return `${((await $.env.get('HOME')) || S.home).replace(/\\/g, '/')}/.local/share/orch/store`
}

export async function sessionDir($: any): Promise<string> {
  return `${await storeRoot($)}/sessions/${S.alias ?? (await $.session.id())}`
}

// The store contract version (version.json), read before the plugin activates.
export async function storeVersion($: any): Promise<any> {
  return readJson($, `${await storeRoot($)}/version.json`)
}

export async function readSession($: any, file: SessionFile, dir: string | undefined = S.dir): Promise<any> {
  return readJson($, `${dir}/${file}`)
}

// A session file with its version, for a later save with an expected version.
export async function readSessionVersioned($: any, file: SessionFile, dir: string | undefined = S.dir): Promise<{ value: any; version: bigint }> {
  const text = await readText($, `${dir}/${file}`)
  return { value: await readSession($, file, dir), version: versionOf(text) }
}

export async function writeSession($: any, file: SessionFile, value: unknown, dir: string | undefined = S.dir, expectedVersion?: bigint): Promise<void> {
  await replace($, `${dir}/${file}`, value, expectedVersion)
}

export async function isEnabled($: any, dir: string | undefined = S.dir): Promise<boolean> {
  return $.fs.exists(`${dir}/enabled`)
}

export async function enable($: any, dir: string): Promise<void> {
  await $.fs.write(`${dir}/enabled`, '')
}

export async function writeHeartbeat($: any, dir: string | undefined = S.dir): Promise<void> {
  await $.fs.write(`${dir}/heartbeat.txt`, await now($))
}

export async function writeMirror($: any, ms: number, uuid: unknown, row: unknown): Promise<void> {
  await $.fs.write(`${S.dir}/mirror/${ms}-${uuid}.json`, json(row))
}

// The phase of the session: active, stopped or archived (lifecycle.phase of session.json, store version 3).
export async function controlState($: any): Promise<string> {
  if (!S.dir) return 'active'
  const entry = await readSession($, 'session.json')
  return typeof entry?.lifecycle?.phase === 'string' ? entry.lifecycle.phase : 'active'
}

// The log of this process (log-<holder>.txt). It keeps the last 100,000 characters when it grows past 200,000.
export async function log($: any, line: string): Promise<void> {
  if (!S.dir) return
  const path = `${S.dir}/log-${S.holder}.txt`
  const old = (await readText($, path)) ?? ''
  const kept = old.length > 200000 ? old.slice(-100000) : old
  await $.fs.write(path, `${kept}${await now($)} ${line}\n`)
}

export async function readPolicy($: any): Promise<any> {
  return S.store ? readJson($, `${S.store}/policy.json`) : undefined
}

// A template file. The store templates root of F1 (<store>/templates/<kind>/) comes first: a store folder with a core
// name replaces the core template. Else the core templates of the tool (<home>/templates/<kind>/).
// The catalogs of the template system, as in C# (Catalog in Orchestrator.Core/Storage/Definition.cs): the folder
// under the templates root, and the marker file that makes a folder a definition.
export const CATALOGS = {
  templates: { folder: '', marker: 'schema.json' },
  modes: { folder: 'modes/', marker: 'mode.json' },
  workflows: { folder: 'workflows/', marker: 'workflow.json' },
} as const

export type CatalogName = keyof typeof CATALOGS

// The C# name rule of a definition (Catalog.IsName). Other names are never read.
const DEFINITION_NAME = /^[a-z][a-z0-9-]{1,31}$/

// One JSON file of a definition. The two roots of LayeredDefinitions in C#: <store>/templates first, if the store
// folder has the marker file of the catalog, else the core templates in <home>/templates.
export async function readDefinition($: any, catalog: CatalogName, name: string, file: string): Promise<any> {
  if (!DEFINITION_NAME.test(name) || !/^[a-z][a-z0-9.-]*\.json$/.test(file)) return undefined
  const { folder, marker } = CATALOGS[catalog]
  if (S.store && (await $.fs.exists(`${S.store}/templates/${folder}${name}/${marker}`)))
    return readJson($, `${S.store}/templates/${folder}${name}/${file}`)
  return readJson($, `${S.home}/templates/${folder}${name}/${file}`)
}

export async function readTemplate($: any, kind: string, file: TemplateFile): Promise<any> {
  return readDefinition($, 'templates', kind, `${file}.json`)
}

// An envelope: the body first, then the envelope. The envelope is the commit point. Both are creates.
export async function createEnvelope($: any, day: string, id: string, body: unknown, envelope: Record<string, unknown>): Promise<void> {
  await create($, `${S.store}/${envelope.body}`, json(body))
  await create($, `${S.store}/events/${day}/${id}.json`, json(envelope))
}

export function bodyPath(day: string, id: string): string {
  return `bodies/${day}/${id}.json`
}

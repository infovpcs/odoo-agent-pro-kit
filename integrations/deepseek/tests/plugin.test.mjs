/**
 * Behavioural test for the odoo-agent-pro-kit DSH plugin.
 *
 * The preset mount validation (`agentPresets.standingKeyFor`) proves the
 * composition loads; it does not prove what the `odoo-kit` row actually
 * registers. This drives `apply()` against a recording stub of the Cordis
 * context and asserts the contributions the integration promises:
 * commands, skills, tools, the lifecycle prompt section, and the guard.
 *
 * Run: node integrations/deepseek/tests/plugin.test.mjs
 */

import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { tmpdir } from 'node:os'
import assert from 'node:assert/strict'

import { apply, inject, name } from '../preset/odoo-kit.mjs'

// The guard is configured from the environment at apply() time. Clear the
// lifts so this suite asserts the DEFAULT posture regardless of the shell it
// runs in — a developer with ODOO_KIT_ALLOW_VCS_WRITE or
// AGENTS_PHASE_AUTHORIZED exported (the repository's own contributor hook
// uses the latter) must not silently change what this test proves.
delete process.env.ODOO_KIT_ALLOW_RAW_ODOO
delete process.env.ODOO_KIT_ALLOW_VCS_WRITE
delete process.env.AGENTS_PHASE_AUTHORIZED

// Connection resolution reads the process environment before any `.env`, so
// clear the Odoo keys too: these tests must assert what the plugin does with a
// workspace `.env`, not what the developer's shell happens to export.
for (const key of Object.keys(process.env)) {
  if (/^(ODOO\d*_|DEFAULT_ODOO_VERSION)/.test(key)) delete process.env[key]
}

const HERE = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = resolve(HERE, '..', '..', '..')

/** Record every contribution one stub context receives. */
function stubContext() {
  const recorded = {
    sections: [],
    tools: [],
    commands: [],
    skills: [],
    guards: [],
    effects: [],
  }
  const ctx = {
    logger: { info() {}, warn() {}, debug() {} },
    get(service) {
      if (service === 'skills') {
        return { register(skill) { recorded.skills.push(skill); return () => {} } }
      }
      if (service === 'commands') {
        return { register(definition) { recorded.commands.push(definition); return () => {} } }
      }
      return undefined
    },
    tools: {
      register(definition) { recorded.tools.push(definition); return () => {} },
      guard(guard) { recorded.guards.push(guard); return () => {} },
    },
    systemPrompt: {
      section(section) { recorded.sections.push(section); return () => {} },
    },
    effect(callback, label) {
      const disposer = callback()
      recorded.effects.push({ label, disposer })
      return disposer
    },
  }
  return { ctx, recorded }
}

/** Let the asynchronous skill discovery settle. */
const settle = () => new Promise(resolvePromise => setTimeout(resolvePromise, 250))

const failures = []
function check(label, fn) {
  try {
    fn()
    console.log(`  ok   ${label}`)
  } catch (error) {
    failures.push(`${label}: ${error.message}`)
    console.log(`  FAIL ${label}: ${error.message}`)
  }
}

/** Async sibling of {@link check}; without it a rejected assertion escapes. */
async function acheck(label, fn) {
  try {
    await fn()
    console.log(`  ok   ${label}`)
  } catch (error) {
    failures.push(`${label}: ${error.message}`)
    console.log(`  FAIL ${label}: ${error.message}`)
  }
}

console.log('odoo-agent-pro-kit DSH plugin')

check('exports name and inject', () => {
  assert.equal(name, 'odoo-agent-pro-kit')
  assert.deepEqual(inject, ['tools', 'systemPrompt'])
})

const { ctx, recorded } = stubContext()
apply(ctx, { repoRoot: REPO_ROOT, defaultOdooVersion: '19.0' })
await settle()

check('registers the lifecycle prompt section once', () => {
  const lifecycle = recorded.sections.filter(section => section.name === 'odoo-agent-pro-kit:lifecycle')
  assert.equal(lifecycle.length, 1)
  assert.equal(typeof lifecycle[0].text, 'string')
  assert.match(lifecycle[0].text, /plan-analysis/)
  assert.match(lifecycle[0].text, /Odoo 17\.0, 18\.0, and 19\.0/)
})

check('registers the five lifecycle commands', () => {
  const names = recorded.commands.map(command => command.name).sort()
  assert.deepEqual(names, ['fleet', 'plan-analysis', 'rules-check-drift', 'start-coding', 'testing'])
  for (const command of recorded.commands) {
    assert.equal(typeof command.handler, 'function')
    assert.ok(command.description.length > 0)
  }
})

check('registers every Odoo tool', () => {
  const names = recorded.tools.map(entry => entry.name).sort()
  assert.deepEqual(names, [
    'odoo_get_fields',
    'odoo_get_model_info',
    'odoo_get_relationships',
    'odoo_get_version_info',
    'odoo_kb_list',
    'odoo_kb_read',
    'odoo_kb_search',
    'odoo_list_all_models',
    'odoo_search_models',
    'odoo_validate_field',
    'odoo_workspace_info',
  ])
})

check('every tool declares an object-rooted parameter schema and an output schema', () => {
  for (const entry of recorded.tools) {
    assert.equal(entry.parameters.type, 'object', `${entry.name} parameters must be an object root`)
    assert.equal(entry.parameters.additionalProperties, false, `${entry.name} must close its parameter object`)
    assert.ok(entry.output !== undefined, `${entry.name} needs an output declaration`)
    assert.equal(typeof entry.output.render, 'function', `${entry.name} needs an output render`)
    assert.ok(entry.output.schema !== undefined, `${entry.name} needs an output schema`)
    assert.equal(typeof entry.execute, 'function', `${entry.name} needs execute`)
  }
})

/**
 * Validate one schema node the way a strict JSON Schema consumer — the model
 * provider — reads it, rather than the way DSH's permissive subset checker
 * does.
 *
 * This check exists because it was missing. The parameters were first written
 * in `defineTool`'s *spec* dialect (`required: true` on a property) but handed
 * to `ctx.tools.register`, which takes already-converted raw JSON Schema. The
 * registry accepted it and the preset mount-validated clean, then every real
 * turn failed with:
 *
 *   Invalid schema for function 'odoo_get_fields': true is not of type "array"
 */
const SCHEMA_KEYWORDS = new Set([
  'type', 'properties', 'required', 'additionalProperties', 'items', 'enum',
  'const', 'oneOf', 'description', 'title', 'default', 'examples',
])

function schemaViolations(node, path) {
  const problems = []
  if (node === null || typeof node !== 'object' || Array.isArray(node)) {
    return [`${path}: schema node must be an object, got ${JSON.stringify(node)}`]
  }
  for (const key of Object.keys(node)) {
    if (!SCHEMA_KEYWORDS.has(key)) problems.push(`${path}.${key}: unsupported or misplaced keyword`)
  }
  if (Object.hasOwn(node, 'required')) {
    if (!Array.isArray(node.required)) {
      problems.push(
        `${path}.required: must be an array of property names (a boolean here reaches the model `
        + `provider as raw JSON Schema), got ${JSON.stringify(node.required)}`,
      )
    } else {
      if (node.type !== 'object') problems.push(`${path}.required: only valid on an object schema`)
      for (const name of node.required) {
        if (typeof name !== 'string') problems.push(`${path}.required: entries must be strings`)
        else if (node.properties !== undefined && !Object.hasOwn(node.properties, name)) {
          problems.push(`${path}.required: "${name}" is not declared in properties`)
        }
      }
    }
  }
  if (node.properties !== undefined) {
    if (typeof node.properties !== 'object' || Array.isArray(node.properties)) {
      problems.push(`${path}.properties: must be an object`)
    } else {
      for (const [name, child] of Object.entries(node.properties)) {
        problems.push(...schemaViolations(child, `${path}.properties.${name}`))
      }
    }
  }
  if (node.type === 'object' && typeof node.additionalProperties !== 'boolean') {
    problems.push(`${path}.additionalProperties: an object schema must declare it as a boolean`)
  }
  if (node.items !== undefined) problems.push(...schemaViolations(node.items, `${path}.items`))
  if (node.oneOf !== undefined) {
    if (!Array.isArray(node.oneOf) || node.oneOf.length < 2) {
      problems.push(`${path}.oneOf: needs at least two branches`)
    } else {
      node.oneOf.forEach((branch, index) => problems.push(...schemaViolations(branch, `${path}.oneOf[${index}]`)))
    }
  }
  if (node.enum !== undefined && !Array.isArray(node.enum)) {
    problems.push(`${path}.enum: must be an array`)
  }
  return problems
}

check('every tool schema is strict JSON Schema the model provider accepts', () => {
  const problems = []
  for (const entry of recorded.tools) {
    problems.push(...schemaViolations(entry.parameters, `${entry.name}.parameters`))
    problems.push(...schemaViolations(entry.output.schema, `${entry.name}.output.schema`))
  }
  assert.deepEqual(problems, [], `tool schema violations:\n  - ${problems.join('\n  - ')}`)
})

check('no tool parameter uses a boolean `required` (the spec-dialect mistake)', () => {
  const walk = (node, path) => {
    if (node === null || typeof node !== 'object') return []
    const found = []
    if (Object.hasOwn(node, 'required') && typeof node.required === 'boolean') {
      found.push(`${path}.required = ${node.required}`)
    }
    for (const [key, value] of Object.entries(node)) {
      found.push(...walk(value, `${path}.${key}`))
    }
    return found
  }
  const offenders = recorded.tools.flatMap(entry => walk(entry.parameters, entry.name))
  assert.deepEqual(offenders, [], `boolean required keywords present: ${offenders.join(', ')}`)
})

check('registers the 25 bundled skills under kebab-case names', () => {
  const skills = recorded.skills
  assert.ok(skills.length >= 20, `expected the bundled skill catalog, got ${skills.length}`)
  for (const skill of skills) {
    assert.match(skill.name, /^[a-z0-9]+(?:-[a-z0-9]+)*$/, `invalid DSH skill name: ${skill.name}`)
    assert.ok(skill.description.length > 0, `${skill.name} needs a description`)
    assert.ok(skill.content.length > 0, `${skill.name} needs a body`)
    assert.equal(skill.source, 'custom')
  }
  const names = skills.map(skill => skill.name)
  assert.ok(names.includes('odoo-19-coding-standard'), 'missing odoo-19-coding-standard')
  assert.ok(names.includes('odoo-17-dependency-context'), 'missing odoo-17-dependency-context')
  for (const odoo20 of ['odoo-20-coding-standard', 'odoo-tools-20', 'odoo-20-dependency-context']) {
    assert.ok(names.includes(odoo20), `missing ${odoo20}`)
  }
  assert.ok(names.includes('odoo-commanding-system'), 'missing odoo-commanding-system')
  assert.equal(new Set(names).size, names.length, 'skill names must be unique after normalization')
})

check('registers exactly one guard', () => {
  assert.equal(recorded.guards.length, 1)
})

const [guard] = recorded.guards
const guardFor = (toolName, args, cwd) => guard({
  name: toolName,
  arguments: args,
  ...(cwd === undefined ? {} : { agent: { session: { header: { cwd } } } }),
})

check('guard blocks a raw odoo-bin run', () => {
  assert.match(guardFor('bash', { command: 'python3 odoo-bin -d db -u sale' }) ?? '', /odoo-bin/)
})

check('guard blocks a direct manage_modules.sh invocation', () => {
  assert.match(guardFor('bash', { command: './manage_modules.sh install sale' }) ?? '', /manage_modules/)
})

check('guard allows the documented bash form and sandboxctl', () => {
  assert.equal(guardFor('bash', { command: 'WORKSPACE_PATH=$(pwd) bash manage_modules.sh install sale' }), undefined)
  assert.equal(guardFor('bash', { command: 'sandbox/bin/sandboxctl module s1 test sale' }), undefined)
})

check('guard blocks VCS writes and destructive cleanup', () => {
  assert.match(guardFor('bash', { command: 'git push origin main' }) ?? '', /git push/)
  assert.match(guardFor('bash', { command: 'git merge main' }) ?? '', /git merge/)
  assert.match(guardFor('bash', { command: 'git merge-base main HEAD' }) ?? 'x', /^$|x/)
  assert.equal(guardFor('bash', { command: 'git merge-base main HEAD' }), undefined)
  assert.match(guardFor('bash', { command: 'rm -rf .sandbox/sessions' }) ?? '', /Destructive/)
})

check('guard blocks writes into an Enterprise source tree', () => {
  assert.match(guardFor('write', { path: '/opt/odoo/enterprise/account/models/x.py' }) ?? '', /Enterprise/)
  assert.equal(guardFor('write', { path: '/opt/odoo/custom/my_module/models/x.py' }), undefined)
})

check('guard ignores unrelated tools', () => {
  assert.equal(guardFor('read', { path: '/tmp/x' }), undefined)
})

check('a .sandbox/AUTHORIZED marker lifts only the VCS and cleanup refusals', () => {
  const workspace = join(tmpdir(), `odoo-kit-marker-${process.pid}`)
  mkdirSync(join(workspace, '.sandbox'), { recursive: true })
  writeFileSync(join(workspace, '.sandbox', 'AUTHORIZED'), '')
  try {
    assert.equal(guardFor('bash', { command: 'git push origin main' }, workspace), undefined)
    assert.equal(guardFor('bash', { command: 'rm -rf .sandbox/sessions' }, workspace), undefined)
    // The raw-run refusal is a different lift and must survive the marker.
    assert.match(guardFor('bash', { command: 'python3 odoo-bin -d db -u sale' }, workspace) ?? '', /odoo-bin/)
    // The marker is scoped to its own workspace.
    assert.match(guardFor('bash', { command: 'git push origin main' }, REPO_ROOT) ?? '', /git push/)
  } finally {
    rmSync(workspace, { recursive: true, force: true })
  }
})

check('AGENTS_PHASE_AUTHORIZED does not lift the agent guard', () => {
  // That variable authorizes this repository's contributor-hook phase
  // workflow. Consulting it here would let a contributor's exported shell
  // silently disable the guard for every agent session.
  process.env.AGENTS_PHASE_AUTHORIZED = '1'
  try {
    const { ctx: envCtx, recorded: envRecorded } = stubContext()
    apply(envCtx, { repoRoot: REPO_ROOT })
    const [envGuard] = envRecorded.guards
    const reason = envGuard({ name: 'bash', arguments: { command: 'git push origin main' } })
    assert.match(reason ?? '', /git push/)
  } finally {
    delete process.env.AGENTS_PHASE_AUTHORIZED
  }
})

check('ODOO_KIT_ALLOW_VCS_WRITE accepts every truthy spelling', () => {
  for (const spelling of ['1', 'true', 'YES', 'On']) {
    process.env.ODOO_KIT_ALLOW_VCS_WRITE = spelling
    try {
      const { ctx: envCtx, recorded: envRecorded } = stubContext()
      apply(envCtx, { repoRoot: REPO_ROOT })
      const [envGuard] = envRecorded.guards
      assert.equal(
        envGuard({ name: 'bash', arguments: { command: 'git push origin main' } }),
        undefined,
        `"${spelling}" should lift the VCS refusal`,
      )
    } finally {
      delete process.env.ODOO_KIT_ALLOW_VCS_WRITE
    }
  }
})

// ── knowledge base round-trip against the real bundle when present ──────────

const kBundle = join(process.env.HOME ?? '', 'odoo-workspaces', 'knowledge-19', 'odoo19-okf')
if (existsSync(kBundle)) {
  const { ctx: kbCtx, recorded: kbRecorded } = stubContext()
  apply(kbCtx, {
    repoRoot: REPO_ROOT,
    defaultOdooVersion: '19.0',
    knowledgeRoots: { '19.0': kBundle, '17.0': join(kBundle, '__missing__') },
  })
  await settle()
  const kbTools = kbRecorded.tools
  const searchTool = kbTools.find(entry => entry.name === 'odoo_kb_search')
  const readEntry = kbTools.find(entry => entry.name === 'odoo_kb_read')
  const listEntry = kbTools.find(entry => entry.name === 'odoo_kb_list')

  const results = await searchTool.execute({ version: '19.0', query: 'compute field depends', limit: 3 }, {})
  check('odoo_kb_search returns ranked Odoo pages from the real bundle', () => {
    assert.ok(Array.isArray(results), 'search must return an array')
    assert.ok(results.length > 0, 'search returned no pages')
    assert.ok(results[0].path.endsWith('.md'), 'result path must be markdown')
    assert.ok(results[0].score > 0)
  })

  const page = await readEntry.execute({ version: '19.0', path: results[0].path, max_chars: 2000 }, {})
  check('odoo_kb_read returns page content with a title', () => {
    assert.equal(page.path, results[0].path)
    assert.ok(page.content.length > 0)
    assert.equal(typeof page.title, 'string')
  })

  await acheck('odoo_kb_read refuses to escape the bundle root', async () => {
    await assert.rejects(() => readEntry.execute({ version: '19.0', path: '../../etc/passwd' }, {}), /escapes/)
  })

  const listing = await listEntry.execute({}, {})
  check('odoo_kb_list reports the configured bundles', () => {
    assert.ok(Array.isArray(listing.bundles))
    assert.equal(listing.bundles.find(entry => entry.version === '19.0')?.exists, true)
  })

  await acheck('a missing bundle fails with an actionable message', async () => {
    await assert.rejects(
      () => readEntry.execute({ version: '17.0', path: 'index.md' }, {}),
      /does not exist/,
    )
  })
} else {
  console.log('  skip knowledge-base round-trip (no bundle at knowledge-19/odoo19-okf)')
}

// ── workspace tool ──────────────────────────────────────────────────────────

const workspaceTool = recorded.tools.find(entry => entry.name === 'odoo_workspace_info')
const workspace = await workspaceTool.execute({}, { agent: { session: { header: { cwd: REPO_ROOT } } } })
check('odoo_workspace_info reports config and detected workspace', () => {
  assert.equal(workspace.kit_root, REPO_ROOT)
  assert.ok(Array.isArray(workspace.connections))
  assert.equal(workspace.connections.length, 4) // one per supported version: 17, 18, 19, 20
  assert.equal(workspace.guard.allow_raw_odoo, false)
  assert.equal(workspace.guard.allow_vcs_write_env, false)
  assert.equal(workspace.guard.vcs_writes_allowed, false)
})

// ── `.env` discovery, the parity gap with the Python/hooks path ─────────────

const CONNECTIONS_WORKSPACE = mkdtempSync(join(tmpdir(), 'odoo-kit-env-'))
writeFileSync(join(CONNECTIONS_WORKSPACE, '.env'), [
  '# comment line',
  '',
  'ODOO_URL=http://localhost:8109',
  'ODOO_DB_NAME=odoo19',
  'ODOO_DB_USER=admin',
  'ODOO_DB_PASSWORD=super-secret-value',
  'export ODOO17_URL="http://localhost:8107"',
  "ODOO17_DB_NAME='odoo17'",
  'ODOO18_DB_NAME=odoo18  # trailing comment',
  'DEFAULT_ODOO_VERSION=17',
].join('\n'))

/** Apply the plugin fresh and run odoo_workspace_info from one workspace. */
async function workspaceInfo(cwd) {
  const { ctx: envCtx, recorded: envRecorded } = stubContext()
  apply(envCtx, { repoRoot: REPO_ROOT })
  const info = envRecorded.tools.find(entry => entry.name === 'odoo_workspace_info')
  return { out: await info.execute({}, { agent: { session: { header: { cwd } } } }), tools: envRecorded.tools }
}

const { out: envWorkspace } = await workspaceInfo(CONNECTIONS_WORKSPACE)

check('resolves Odoo connections from the workspace .env', () => {
  const byVersion = Object.fromEntries(envWorkspace.connections.map(entry => [entry.version, entry]))
  assert.equal(byVersion['19.0'].database, 'odoo19', 'generic ODOO_DB_NAME should apply to 19.0')
  assert.equal(byVersion['19.0'].url, 'http://localhost:8109')
  assert.equal(byVersion['19.0'].credentials_present, true)
  // Version-prefixed keys win, and the quoted / exported forms parse.
  assert.equal(byVersion['17.0'].url, 'http://localhost:8107')
  assert.equal(byVersion['17.0'].database, 'odoo17')
  // An inline comment is not part of the value.
  assert.equal(byVersion['18.0'].database, 'odoo18')
})

check('DEFAULT_ODOO_VERSION from .env selects the default version', () => {
  assert.equal(envWorkspace.default_version, '17.0')
})

check('the process environment outranks any .env layer', async () => {
  process.env.ODOO19_DB_NAME = 'from-process'
  try {
    const { out } = await workspaceInfo(CONNECTIONS_WORKSPACE)
    const nineteen = out.connections.find(entry => entry.version === '19.0')
    assert.equal(nineteen.database, 'from-process')
  } finally {
    delete process.env.ODOO19_DB_NAME
  }
})

check('no password reaches the model through odoo_workspace_info', () => {
  const serialized = JSON.stringify(envWorkspace)
  assert.ok(!serialized.includes('super-secret-value'), 'the .env password leaked into tool output')
  assert.ok(!/password/i.test(serialized), 'the output exposes a password field')
})

check('a workspace without a .env reports connections as unconfigured', async () => {
  const bare = mkdtempSync(join(tmpdir(), 'odoo-kit-bare-'))
  try {
    const { out } = await workspaceInfo(bare)
    assert.equal(out.connections.every(entry => entry.credentials_present === false), true)
  } finally {
    rmSync(bare, { recursive: true, force: true })
  }
})

check('a malformed .env does not break resolution', async () => {
  const broken = mkdtempSync(join(tmpdir(), 'odoo-kit-broken-'))
  writeFileSync(join(broken, '.env'), 'not a pair\n=novalue\nOK_KEY=value\n"bad"=x\n')
  try {
    const { out } = await workspaceInfo(broken)
    assert.equal(out.connections.length, 4, 'a broken .env must not fail the call')
  } finally {
    rmSync(broken, { recursive: true, force: true })
  }
})

rmSync(CONNECTIONS_WORKSPACE, { recursive: true, force: true })

// ── command handler submits the workflow as a user message ──────────────────

const planCommand = recorded.commands.find(command => command.name === 'plan-analysis')
const submitted = []
const result = await planCommand.handler({
  rawInput: '19.0 sale_custom',
  agent: { session: { header: { cwd: REPO_ROOT } }, followup: message => submitted.push(message) },
})
check('/plan-analysis submits its instruction body as a user message', () => {
  assert.equal(result.kind, 'success')
  assert.equal(submitted.length, 1)
  assert.equal(submitted[0].role, 'user')
  assert.equal(submitted[0].source.kind, 'user')
  assert.match(submitted[0].content[0].text, /Odoo version: 19\.0/)
  assert.match(submitted[0].content[0].text, /Module\/argument: sale_custom/)
})

await acheck('/rules-check-drift accepts a diff range instead of a version', async () => {
  const drift = recorded.commands.find(command => command.name === 'rules-check-drift')
  const seen = []
  const outcome = await drift.handler({
    rawInput: 'main...HEAD',
    agent: { session: { header: { cwd: REPO_ROOT } }, followup: message => seen.push(message) },
  })
  assert.equal(outcome.kind, 'success')
  assert.match(seen[0].content[0].text, /Module\/argument: main\.\.\.HEAD/)
})

// ── lossless-JSON seam: absent Odoo attributes must not surface as undefined ─
//
// DSH snapshots every tool body's value into lossless JSON and rejects the call
// outright — `tool returned invalid output: value is not lossless JSON` — when
// any member is `undefined`. Odoo's `fields_get` returns only the attributes a
// field actually declares, so requesting `relation`/`help` yields an ABSENT key
// for every scalar field.
//
// The checks above all call `execute()` directly and inspect the returned
// object, which is exactly why this shipped broken: nothing exercised the seam,
// so `undefined` looked fine in-process while every live call failed. These
// checks reproduce DSH's two rejection rules instead.

/** Locate the first `undefined` member, the way DSH's walk does. */
function findUndefined(value, path = '$') {
  if (value === undefined) return path
  if (value === null || typeof value !== 'object') return null
  if (Array.isArray(value)) {
    for (let index = 0; index < value.length; index += 1) {
      const hit = findUndefined(value[index], `${path}[${index}]`)
      if (hit !== null) return hit
    }
    return null
  }
  for (const [key, member] of Object.entries(value)) {
    const hit = findUndefined(member, `${path}.${key}`)
    if (hit !== null) return hit
  }
  return null
}

/** Assert a tool body's value could cross DSH's lossless-JSON seam. */
function assertLossless(label, value) {
  const hit = findUndefined(value)
  assert.equal(hit, null, `${label}: \`undefined\` at ${hit} is not lossless JSON`)
  assert.deepStrictEqual(
    JSON.parse(JSON.stringify(value)),
    value,
    `${label}: value does not survive a JSON round-trip`,
  )
}

// Shaped like a real Odoo 19 `fields_get` reply: scalar fields carry no
// `relation`/`help`/`readonly` key at all; only many2one carries `relation`.
const FIELDS_GET_REPLY = {
  name: { string: 'Name', type: 'char', required: true },
  state: { string: 'Status', type: 'selection' },
  partner_id: { string: 'Customer', type: 'many2one', relation: 'res.partner' },
}
const ID_FIELD = { string: 'ID', type: 'integer', required: false, readonly: true }

const realFetch = globalThis.fetch
globalThis.fetch = async (_url, init) => {
  const { params } = JSON.parse(init.body)
  const positional = params.args?.[5]
  const narrowedTo = Array.isArray(positional) && positional.length > 0
  const requested = narrowedTo
    ? positional.filter(key => key in FIELDS_GET_REPLY)
    : Object.keys(FIELDS_GET_REPLY)
  // A single-field `fields_get` narrows to that field — except that Odoo answers
  // a *many2one* request with `id` as well, and puts it FIRST. Verified live
  // against Odoo 19: fields_get(['partner_id']) -> ['id', 'partner_id']. A stub
  // that returned only the requested key is what let the "read the first entry"
  // bug ship, so this reproduces the real shape instead.
  const relational = requested.some(key => FIELDS_GET_REPLY[key].type.endsWith('2one'))
  const narrowed = {
    ...(narrowedTo && relational ? { id: ID_FIELD } : {}),
    ...Object.fromEntries(requested.map(key => [key, FIELDS_GET_REPLY[key]])),
  }
  const result = params.service === 'common' ? 2 : narrowed
  return { json: async () => ({ jsonrpc: '2.0', id: 1, result }) }
}

// A dedicated stub URL keeps this session out of the module's connection cache.
process.env.ODOO19_URL = 'http://odoo-stub.invalid'
process.env.ODOO19_DB_NAME = 'stub-db'
process.env.ODOO19_DB_USER = 'stub-user'
process.env.ODOO19_DB_PASSWORD = 'stub-pass'

const DETECTED_WORKSPACE = mkdtempSync(join(tmpdir(), 'odoo-kit-lossless-'))
mkdirSync(join(DETECTED_WORKSPACE, '19.0'), { recursive: true })

try {
  const { ctx: seamCtx, recorded: seamRecorded } = stubContext()
  apply(seamCtx, { repoRoot: REPO_ROOT, defaultOdooVersion: '19.0' })
  const toolNamed = name => seamRecorded.tools.find(entry => entry.name === name)
  const seamExec = { agent: { session: { header: { cwd: DETECTED_WORKSPACE } } } }

  await acheck('odoo_get_fields emits null, never undefined, for absent attributes', async () => {
    const result = await toolNamed('odoo_get_fields')
      .execute({ model_name: 'sale.order', version: '19.0' }, seamExec)
    assertLossless('odoo_get_fields', result)
    const byName = Object.fromEntries(result.fields.map(field => [field.name, field]))
    assert.equal(byName.partner_id.relation, 'res.partner')
    assert.equal(byName.name.relation, null, 'an absent relation must be null')
    assert.equal(byName.name.help, null, 'an absent help must be null')
    assert.equal(byName.name.readonly, false)
  })

  await acheck('odoo_validate_field survives the lossless-JSON seam', async () => {
    const result = await toolNamed('odoo_validate_field')
      .execute({ model_name: 'sale.order', field_name: 'partner_id', version: '19.0' }, seamExec)
    assertLossless('odoo_validate_field', result)
    assert.equal(result.exists, true)
    // Odoo answers a many2one request with `id` first; the tool must describe the
    // field that was asked for, not whichever key came back first.
    assert.equal(result.field.name, 'partner_id', 'must describe the requested field, not `id`')
    assert.equal(result.field.type, 'many2one')
    assert.equal(result.field.relation, 'res.partner')
    assert.equal(result.field.help, null)
  })

  await acheck('odoo_validate_field reports a fabricated field as absent', async () => {
    const result = await toolNamed('odoo_validate_field')
      .execute({ model_name: 'sale.order', field_name: 'no_such_field_xyz', version: '19.0' }, seamExec)
    assertLossless('odoo_validate_field', result)
    assert.equal(result.exists, false, 'an unknown field must not be reported as existing')
    assert.equal(result.field, 'no_such_field_xyz')
  })

  await acheck('odoo_workspace_info survives the lossless-JSON seam', async () => {
    const result = await toolNamed('odoo_workspace_info').execute({}, seamExec)
    assertLossless('odoo_workspace_info', result)
    // The probe workspace holds a `19.0/` directory but no `.sandbox/session.json`,
    // so detection reports the directory source with no module.
    assert.equal(result.detected.source, 'workspace-directory')
    assert.equal(result.detected.module, null)
  })
} finally {
  globalThis.fetch = realFetch
  for (const key of ['ODOO19_URL', 'ODOO19_DB_NAME', 'ODOO19_DB_USER', 'ODOO19_DB_PASSWORD']) {
    delete process.env[key]
  }
  rmSync(DETECTED_WORKSPACE, { recursive: true, force: true })
}

console.log('')
if (failures.length > 0) {
  console.error(`${failures.length} check(s) failed`)
  process.exit(1)
}
console.log('OK: all odoo-agent-pro-kit DSH plugin checks passed.')

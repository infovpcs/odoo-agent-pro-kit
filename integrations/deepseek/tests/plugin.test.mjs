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

import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs'
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

check('registers the 22 bundled skills under kebab-case names', () => {
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
  assert.equal(workspace.connections.length, 3)
  assert.equal(workspace.guard.allow_raw_odoo, false)
  assert.equal(workspace.guard.allow_vcs_write_env, false)
  assert.equal(workspace.guard.vcs_writes_allowed, false)
})

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

console.log('')
if (failures.length > 0) {
  console.error(`${failures.length} check(s) failed`)
  process.exit(1)
}
console.log('OK: all odoo-agent-pro-kit DSH plugin checks passed.')

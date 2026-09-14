/**
 * odoo-agent-pro-kit — DeepSeek Harness (DSH) agent-plane plugin.
 *
 * One Cordis plugin row that turns a DSH session into an Odoo 17.0/18.0/19.0
 * custom-application development session, mirroring what the native Hermes
 * plugin (`plugin/__init__.py`) and the Claude Code plugin (`plugin/`) give
 * those agents:
 *
 *   - the five lifecycle slash commands from `plugin/commands/*.md`
 *     (`/plan-analysis`, `/start-coding`, `/testing`, `/fleet`,
 *     `/rules-check-drift`), each submitting its instruction body as a
 *     model-visible user message;
 *   - all 22 bundled skills, re-registered under DSH's kebab-case skill
 *     grammar (upstream frontmatter names use underscores, which
 *     `dsh-skill-filesystem` silently ignores);
 *   - live model discovery (`odoo_*` tools) over XML-RPC / JSON-RPC-2.0,
 *     the in-process equivalent of `plugin/odoo_mcp/`;
 *   - offline documentation retrieval (`odoo_kb_*` tools) over the per-version
 *     OKF knowledge bundles;
 *   - a lifecycle prompt section plus Odoo workspace/version detection;
 *   - a tool guard mirroring the deterministic pipeline hooks in
 *     `plugin/hooks/checks/guard.py`.
 *
 * It is plain ESM using only `node:` builtins. A user preset lives under
 * `$DSH_HOME/.agent-presets/`, where Node's upward `node_modules` walk never
 * reaches the harness's own dependencies, so this file must not import any
 * bare package — every harness service it touches arrives through `ctx`.
 *
 * The row registers into the scoped `tools`, `commands`, `skills`, and
 * `systemPrompt` registries and publishes no service of its own, so it sits
 * loose in the preset composition with no `isolate` realm.
 *
 * @module odoo-agent-pro-kit
 */

import { existsSync, readFileSync } from 'node:fs'
import { readFile, readdir } from 'node:fs/promises'
import { randomUUID } from 'node:crypto'
import { homedir } from 'node:os'
import { basename, join, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'

/** Stable Loader identity for this row. */
export const name = 'odoo-agent-pro-kit'

/** Host services this row contributes to. */
export const inject = ['tools', 'systemPrompt']

/** Odoo versions this kit covers, newest first. */
const VERSIONS = ['19.0', '18.0', '17.0']

/** Short forms accepted on the command line, mapped to the full version. */
const VERSION_ALIASES = {
  '17': '17.0', '18': '18.0', '19': '19.0',
  '17.0': '17.0', '18.0': '18.0', '19.0': '19.0',
}

/** Context/section orders from `dsh-system-prompt`'s centrally allocated table. */
const LIFECYCLE_SECTION_ORDER = 300

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

/** Build one durable user message without importing `@deepseek-ai/dsh-llm`. */
function userMessage(text) {
  return Object.freeze({
    id: randomUUID(),
    role: 'user',
    content: Object.freeze([Object.freeze({ type: 'text', text })]),
    source: Object.freeze({ kind: 'user' }),
  })
}

/** Render one model-facing text tool result. */
function textResult(text) {
  return [{ type: 'text', text }]
}

/**
 * Define one tool definition without `@deepseek-ai/dsh-tools`' `defineTool`.
 * The registry validates `parameters` against its supported JSON Schema subset,
 * and `execute` must return a value matching `output.schema`.
 */
function tool(definition) {
  const { render, outputSchema, ...rest } = definition
  return {
    ...rest,
    output: {
      schema: outputSchema,
      render: (_args, value) => textResult(render === undefined ? String(value) : render(value)),
    },
  }
}

/** Human-readable rendering of an unknown thrown value. */
function errorText(error) {
  if (error === undefined || error === null) return 'unknown error'
  return error instanceof Error ? error.message : String(error)
}

/** JSON text for a model-facing result. */
function jsonText(value) {
  return JSON.stringify(value, null, 2)
}

/** The truthy spellings `plugin/hooks/checks/common.py` accepts. */
function truthyEnv(value) {
  return ['1', 'true', 'yes', 'on'].includes(String(value ?? '').trim().toLowerCase())
}

/**
 * Whether the user authorized VCS writes for this workspace.
 *
 * Mirrors `plugin/hooks/checks/authz.py::vcs_write_allowed`: either the
 * environment lift, or a `.sandbox/AUTHORIZED` marker the user created after
 * approving the operation.
 */
function vcsMarkerPresent(cwd) {
  if (typeof cwd !== 'string' || cwd === '') return false
  return existsSync(join(cwd, '.sandbox', 'AUTHORIZED'))
}

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/** Replace a leading `~` with the user's home directory. */
function expandHome(path) {
  const text = String(path)
  if (text === '~') return homedir()
  if (text.startsWith('~/')) return join(homedir(), text.slice(2))
  return text
}

/** This plugin's own directory — the installed preset directory. */
const PRESET_DIRECTORY = fileURLToPath(new URL('.', import.meta.url))

/**
 * Default kit root: the absolute path the installer recorded beside this file.
 *
 * Keeping the composition itself path-free makes it portable across machines;
 * `install.sh` writes `kit-root.txt` next to it after copying. An explicit
 * `repoRoot` in the row always wins.
 */
function recordedKitRoot() {
  const marker = join(PRESET_DIRECTORY, 'kit-root.txt')
  if (!existsSync(marker)) return undefined
  try {
    const value = readFileSync(marker, 'utf8').trim()
    return value === '' ? undefined : resolve(expandHome(value))
  } catch {
    return undefined
  }
}

/**
 * Default knowledge-base bundle for a version, in the layout the kit's
 * `knowledge-*` checkouts use. Only used when the row configures none.
 */
function defaultKnowledgeRoot(version) {
  const short = version.split('.')[0]
  const candidate = join(homedir(), 'odoo-workspaces', `knowledge-${short}`, `odoo${short}-okf`)
  return existsSync(candidate) ? candidate : undefined
}

/**
 * Resolve this row's configuration into absolute paths and connection specs.
 *
 * Nothing here is required: an unconfigured preset still registers skills,
 * commands, the prompt section, and the guard, and every tool answers with an
 * actionable "not configured" message instead of throwing.
 */
function resolveConfig(config) {
  const raw = config ?? {}
  const repoRoot = raw.repoRoot === undefined
    ? recordedKitRoot()
    : resolve(expandHome(raw.repoRoot))

  const knowledgeRoots = {}
  for (const version of VERSIONS) {
    const value = raw.knowledgeRoots?.[version]
    if (typeof value === 'string' && value.trim() !== '') {
      knowledgeRoots[version] = resolve(expandHome(value))
      continue
    }
    const fallback = defaultKnowledgeRoot(version)
    if (fallback !== undefined) knowledgeRoots[version] = fallback
  }

  const defaultOdooVersion = VERSION_ALIASES[String(raw.defaultOdooVersion ?? '')]
    ?? (VERSIONS.includes(String(raw.defaultOdooVersion)) ? String(raw.defaultOdooVersion) : undefined)

  const odoo = {}
  for (const version of VERSIONS) {
    const entry = raw.odoo?.[version] ?? {}
    const prefix = `ODOO${version.split('.')[0]}`
    odoo[version] = {
      url: entry.url ?? process.env[`${prefix}_URL`] ?? process.env.ODOO_URL,
      db: entry.db ?? process.env[`${prefix}_DB_NAME`] ?? process.env.ODOO_DB_NAME,
      user: entry.user ?? process.env[`${prefix}_DB_USER`] ?? process.env.ODOO_DB_USER ?? 'admin',
      password: entry.password
        ?? process.env[entry.passwordEnv ?? `${prefix}_DB_PASSWORD`]
        ?? process.env.ODOO_DB_PASSWORD,
    }
  }

  return {
    repoRoot,
    knowledgeRoots,
    defaultOdooVersion,
    odoo,
    // Same truthy spellings and the same variables as `plugin/hooks/checks/`
    // (`common.py` for the raw-run lift, `authz.py` for the VCS lift). The
    // contributor hook's `AGENTS_PHASE_AUTHORIZED` is deliberately NOT
    // consulted here: it authorizes a repository phase workflow, not an
    // agent's shell, and a contributor's exported shell would otherwise
    // silently disable this guard.
    allowRawOdoo: truthyEnv(process.env.ODOO_KIT_ALLOW_RAW_ODOO),
    allowVcsWriteEnv: truthyEnv(process.env.ODOO_KIT_ALLOW_VCS_WRITE),
  }
}

/**
 * Detect the Odoo version and module of the session workspace.
 *
 * The sandbox session manifest wins when present (it is authoritative for a
 * Docker Sandbox session); otherwise a version-named directory in the working
 * directory is the signal, exactly as the native Hermes session-start hook
 * does.
 */
function detectWorkspace(cwd) {
  const root = resolve(cwd ?? process.cwd())
  const manifest = join(root, '.sandbox', 'session.json')
  if (existsSync(manifest)) {
    try {
      const data = JSON.parse(readFileSync(manifest, 'utf8'))
      if (data?.odoo_version !== undefined) {
        return {
          source: 'sandbox-session',
          version: VERSION_ALIASES[String(data.odoo_version).split('.')[0]] ?? String(data.odoo_version),
          module: data.module,
          sessionId: data.session_id,
          status: data.status,
        }
      }
    } catch {
      // A malformed manifest degrades to directory detection, never a failure.
    }
  }
  for (const version of VERSIONS) {
    if (existsSync(join(root, version))) {
      return { source: 'workspace-directory', version, module: undefined }
    }
  }
  return { source: 'unknown', version: undefined, module: undefined }
}

// ---------------------------------------------------------------------------
// Skills
// ---------------------------------------------------------------------------

/**
 * Normalize one upstream skill name to DSH's kebab-case grammar.
 *
 * Upstream names are Hermes/Claude-Code flavoured (`odoo_17_coding_standard`);
 * `dsh-skill-filesystem` accepts only `/^[a-z0-9]+(?:-[a-z0-9]+)*$/` and
 * silently drops anything else, so every registered name goes through here.
 */
function toSkillName(raw, fallback) {
  const source = String(raw ?? fallback ?? '')
  const kebab = source
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-')
  return kebab
}

/** Parse the leading YAML frontmatter of a SKILL.md / command markdown file. */
function parseFrontmatter(raw) {
  const text = String(raw)
  if (!text.startsWith('---')) return { data: {}, body: text, hasFrontmatter: false }
  const end = text.indexOf('\n---', 3)
  if (end === -1) return { data: {}, body: text, hasFrontmatter: false }
  const block = text.slice(3, end)
  const body = text.slice(text.indexOf('\n', end + 1) + 1)
  const data = {}
  for (const line of block.split('\n')) {
    const match = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line)
    if (match === null) continue
    let value = match[2].trim()
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1)
    }
    data[match[1]] = value
  }
  return { data, body: body.replace(/^\s*\n/, ''), hasFrontmatter: true }
}

/** Discover `<skillsDir>/<name>/SKILL.md` bundles. */
async function discoverSkills(skillsDir) {
  if (skillsDir === undefined || !existsSync(skillsDir)) return []
  const found = []
  for (const entry of await readdir(skillsDir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue
    const directory = join(skillsDir, entry.name)
    const file = join(directory, 'SKILL.md')
    if (!existsSync(file)) continue
    try {
      const raw = await readFile(file, 'utf8')
      const { data, body } = parseFrontmatter(raw)
      const skillName = toSkillName(data.name, entry.name)
      if (skillName === '') continue
      found.push({
        name: skillName,
        description: data.description ?? `Odoo agent skill ${entry.name}.`,
        whenToUse: data.whenToUse,
        content: body.trim(),
        path: file,
        directory,
        upstreamName: data.name ?? entry.name,
      })
    } catch {
      // One unreadable skill must never take the whole catalog down.
    }
  }
  return found.sort((left, right) => left.name.localeCompare(right.name))
}

// ---------------------------------------------------------------------------
// Commands
// ---------------------------------------------------------------------------

/** Split an optional leading version token off a command argument string. */
function parseVersionAndRest(rawArgs) {
  const input = String(rawArgs ?? '').trim()
  const [first, ...rest] = input.split(/\s+/)
  const version = VERSION_ALIASES[first]
  if (version !== undefined) return { version, rest: rest.join(' ').trim() }
  return { version: undefined, rest: input }
}

/**
 * Read one `plugin/commands/<name>.md` body.
 *
 * A missing file degrades to a short built-in prompt so the command still works
 * from a preset installed without the repository beside it.
 */
async function readCommandPrompt(repoRoot, commandFile) {
  if (repoRoot !== undefined) {
    const path = join(repoRoot, 'plugin', 'commands', commandFile)
    if (existsSync(path)) {
      const { body } = parseFrontmatter(await readFile(path, 'utf8'))
      return body.trim()
    }
  }
  return undefined
}

// ---------------------------------------------------------------------------
// Odoo JSON-RPC client
// ---------------------------------------------------------------------------

/** One pooled Odoo session, keyed by version. */
const sessions = new Map()

/** Authenticate against one Odoo database and return its uid. */
async function odooLogin(spec, signal) {
  const call = async (method, args) => {
    const response = await fetch(new URL('/jsonrpc', spec.url), {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { service: 'common', method, args }, id: randomUUID() }),
      signal,
    })
    const payload = await response.json()
    if (payload.error !== undefined) {
      throw new Error(payload.error?.data?.message ?? payload.error?.message ?? `Odoo ${method} failed`)
    }
    return payload.result
  }
  try {
    return await call('login', [spec.db, spec.user, spec.password])
  } catch (error) {
    // Odoo 18/19 renamed `login` to `authenticate`; keep both working.
    if (!/login|method|not found|unknown/i.test(errorText(error))) throw error
    return await call('authenticate', [spec.db, spec.user, spec.password, {}])
  }
}

/** Return one authenticated `{ uid, spec }` session for a version. */
async function odooSession(version, config, signal) {
  const spec = config.odoo[version]
  if (spec === undefined || !spec.url || !spec.db) {
    throw new Error(
      `Odoo ${version} is not configured. Set ODOO${version.split('.')[0]}_URL, `
      + `ODOO${version.split('.')[0]}_DB_NAME, ODOO${version.split('.')[0]}_DB_USER and `
      + `ODOO${version.split('.')[0]}_DB_PASSWORD (or ODOO_URL/ODOO_DB_NAME/ODOO_DB_USER/ODOO_DB_PASSWORD) `
      + 'and restart the session.',
    )
  }
  const key = `${version}|${spec.url}|${spec.db}|${spec.user}`
  const cached = sessions.get(key)
  if (cached !== undefined) return cached
  const session = { uid: await odooLogin(spec, signal), spec }
  sessions.set(key, session)
  return session
}

/** Call `object.execute_kw` for one version. */
async function executeKw(version, config, model, method, positional = [], kwargs = {}, signal) {
  const { uid, spec } = await odooSession(version, config, signal)
  const response = await fetch(new URL('/jsonrpc', spec.url), {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      params: {
        service: 'object',
        method: 'execute_kw',
        args: [spec.db, uid, spec.password, model, method, positional, kwargs],
      },
      id: randomUUID(),
    }),
    signal,
  })
  const payload = await response.json()
  if (payload.error !== undefined) {
    const data = payload.error?.data
    throw new Error(data?.message ?? payload.error?.message ?? `Odoo ${model}.${method} failed`)
  }
  return payload.result
}

/** Resolve the working directory of the agent behind one tool or command call. */
function agentCwd(agent) {
  const cwd = agent?.session?.header?.cwd
  return typeof cwd === 'string' && cwd !== '' ? cwd : process.cwd()
}

/** Resolve the version a tool call should use. */
function pickVersion(requested, config, cwd) {
  const alias = VERSION_ALIASES[String(requested ?? '')] ?? (VERSIONS.includes(String(requested)) ? String(requested) : undefined)
  if (alias !== undefined) return alias
  if (config.defaultOdooVersion !== undefined) return config.defaultOdooVersion
  return detectWorkspace(cwd).version ?? '19.0'
}

/** Coerce a JSON-RPC field-type map into a stable model-facing list. */
function fieldList(fieldsGet) {
  return Object.entries(fieldsGet ?? {}).map(([fieldName, info]) => ({
    name: fieldName,
    type: info.type,
    string: info.string,
    required: info.required === true,
    readonly: info.readonly === true,
    relation: info.relation,
    help: info.help,
  }))
}

// ---------------------------------------------------------------------------
// Knowledge base (OKF bundles)
// ---------------------------------------------------------------------------

const KB_FILE_CACHE = new Map()

/** Recursively list the markdown pages of one OKF bundle (cached per root). */
async function kbMarkdownFiles(root) {
  const cached = KB_FILE_CACHE.get(root)
  if (cached !== undefined) return cached
  const files = []
  const walk = async (directory) => {
    let entries
    try {
      entries = await readdir(directory, { withFileTypes: true })
    } catch {
      return
    }
    for (const entry of entries) {
      if (entry.name.startsWith('.') || entry.name === 'attachments' || entry.name === 'node_modules') continue
      const path = join(directory, entry.name)
      if (entry.isDirectory()) await walk(path)
      else if (entry.name.endsWith('.md')) files.push(path)
    }
  }
  await walk(root)
  files.sort()
  KB_FILE_CACHE.set(root, files)
  return files
}

/** Resolve a configured knowledge root, or throw an actionable error. */
function kbRoot(version, config) {
  const root = config.knowledgeRoots[version]
  if (root === undefined) {
    throw new Error(
      `No knowledge base is configured for Odoo ${version}. Set knowledgeRoots["${version}"] in the `
      + 'preset row (see integrations/deepseek/INSTALL.md) to an OKF bundle such as '
      + `~/odoo-workspaces/knowledge-${version.split('.')[0]}/odoo${version.split('.')[0]}-okf.`,
    )
  }
  if (!existsSync(root)) throw new Error(`The configured Odoo ${version} knowledge base does not exist: ${root}`)
  return root
}

/** Refuse paths that escape the bundle root. */
function safeKbPath(root, requested) {
  const target = resolve(root, requested ?? '')
  if (target !== root && !target.startsWith(root + sep)) {
    throw new Error(`Path "${requested}" escapes the knowledge base root.`)
  }
  return target
}

/** Extract the `title:` of an OKF page, falling back to its first heading. */
function kbTitle(raw, fallback) {
  const match = /^title:\s*"?(.*?)"?\s*$/m.exec(raw.slice(0, 2000))
  if (match !== null && match[1].trim() !== '') return match[1].trim()
  const heading = /^#\s+(.+)$/m.exec(raw)
  return heading === null ? fallback : heading[1].trim()
}

/** Score one page against the query terms and return a short snippet. */
function kbScore(raw, terms) {
  const haystack = raw.toLowerCase()
  let score = 0
  for (const term of terms) {
    let index = haystack.indexOf(term)
    let hits = 0
    while (index !== -1 && hits < 40) {
      hits += 1
      index = haystack.indexOf(term, index + term.length)
    }
    if (hits === 0) return 0
    score += Math.min(hits, 20)
  }
  const first = haystack.indexOf(terms[0])
  const snippet = raw.slice(Math.max(0, first - 160), Math.max(0, first - 160) + 320).replace(/\s+/g, ' ').trim()
  return { score, snippet }
}

// ---------------------------------------------------------------------------
// Tool guard — the DSH equivalent of plugin/hooks/checks/guard.py
// ---------------------------------------------------------------------------

const ODOO_BIN_RE = /(?:^|[\n;&|]|\bpython3?\s+)\s*(?:[\w./-]*\/)?odoo[-_ ]bin\b/
const SANDBOXCTL_RE = /\bsandboxctl\b/
const MANAGE_DIRECT_RE = /(?:^|[\n;&|]|\bsh\s+|\bzsh\s+)\s*(?:\.\/)?manage_modules\.sh\b/
const MANAGE_BASH_RE = /\bbash\s+(?:-\S+\s+)*(?:\.\/)?manage_modules\.sh\b/
const VCS_WRITE_RES = [
  [/\bgit\s+push\b/, 'git push'],
  [/\bgit\s+merge\b(?!-)/, 'git merge'],
  [/\bgit\s+tag\b(?!\s+(?:-l\b|--list\b|-n\d*\b))/, 'git tag'],
  [/\bgit\s+commit\b[^\n]*--amend\b/, 'git commit --amend'],
  [/\bgh\s+pr\s+(?:create|merge)\b/, 'gh pr create/merge'],
  [/\bgh\s+release\b/, 'gh release'],
]
const DESTRUCTIVE_RES = [
  /\bsbx\s+(?:rm|delete|destroy)\b/,
  /\bdocker\s+system\s+prune\b/,
  /\bdocker\s+volume\s+rm\b/,
  /\brm\s+-rf?\b[^\n]*\.sandbox\b/,
]

/** Extract a shell command string from whatever shape a bash tool uses. */
function commandOf(args) {
  if (args === undefined || args === null || typeof args !== 'object') return undefined
  for (const key of ['command', 'cmd', 'script', 'input']) {
    if (typeof args[key] === 'string') return args[key]
  }
  return undefined
}

/**
 * Whether VCS writes and destructive cleanup are authorized right now.
 *
 * The environment lift was resolved once at apply time; the marker is read per
 * call against the calling agent's workspace, so a user who creates
 * `.sandbox/AUTHORIZED` mid-session is honoured without a restart — and one
 * who removes it is refused again.
 */
function vcsWritesAllowed(config, agent) {
  return config.allowVcsWriteEnv || vcsMarkerPresent(agentCwd(agent))
}

/** First denial reason for one tool execution, or undefined to allow it. */
function guardReason(execution, config) {
  const toolName = execution?.name
  const args = execution?.arguments
  if (typeof toolName !== 'string') return undefined

  if (/bash|shell|pwsh|terminal|exec/i.test(toolName)) {
    const command = commandOf(args)
    if (command === undefined) return undefined
    if (!config.allowRawOdoo) {
      if (ODOO_BIN_RE.test(command) && !SANDBOXCTL_RE.test(command)) {
        return 'Raw `odoo-bin` execution is not allowed from an agent. Route module install/update/test through '
          + '`sandbox/bin/sandboxctl module <session> install|update|test <module>` (Docker Sandbox) or '
          + '`WORKSPACE_PATH=$(pwd) bash manage_modules.sh install|update <module>` (local). '
          + 'The user can set ODOO_KIT_ALLOW_RAW_ODOO=1 to lift this.'
      }
      if (MANAGE_DIRECT_RE.test(command) && !MANAGE_BASH_RE.test(command)) {
        return '`manage_modules.sh` must be invoked as `bash manage_modules.sh …` — the macOS default shell is zsh, '
          + 'where `./manage_modules.sh` fails. The user can set ODOO_KIT_ALLOW_RAW_ODOO=1 to lift this.'
      }
    }
    if (!vcsWritesAllowed(config, execution?.agent)) {
      for (const [pattern, label] of VCS_WRITE_RES) {
        if (pattern.test(command)) {
          return `\`${label}\` requires explicit user authorization. The user can set ODOO_KIT_ALLOW_VCS_WRITE=1 `
            + 'or create a `.sandbox/AUTHORIZED` marker in the workspace to lift this.'
        }
      }
      for (const pattern of DESTRUCTIVE_RES) {
        if (pattern.test(command)) {
          return 'Destructive sandbox/Docker cleanup requires explicit user authorization. '
            + 'The user can set ODOO_KIT_ALLOW_VCS_WRITE=1 or create a `.sandbox/AUTHORIZED` marker to lift this.'
        }
      }
    }
  }

  if (/write|edit/i.test(toolName)) {
    const path = typeof args?.path === 'string' ? args.path : (typeof args?.file_path === 'string' ? args.file_path : '')
    if (/\/enterprise\/|\\enterprise\\/i.test(path)) {
      return 'Writing into an Odoo Enterprise source tree is never allowed from this kit: licensed Enterprise source '
        + 'must not be fetched, mounted, or modified. Enter the Odoo Enterprise *dependency* by name only.'
    }
  }

  return undefined
}

// ---------------------------------------------------------------------------
// Prompt text
// ---------------------------------------------------------------------------

/** The lifecycle section body, assembled once per apply(). */
function lifecycleSectionText(config) {
  const root = config.repoRoot ?? '(repository root not configured)'
  return [
    'Odoo Agent Pro Kit is mounted for this session. You are working on Odoo custom application',
    'development with version-aware lifecycle coverage for Odoo 17.0, 18.0, and 19.0.',
    '',
    'Lifecycle commands (each submits its full workflow instructions as a user message):',
    '  /plan-analysis <17|18|19> [module]   requirement analysis, model discovery, PRD generation',
    '  /start-coding <17|18|19> [module]    task-loop implementation with backend tests per task',
    '  /testing <17|18|19> [module]         frontend UI tests and documentation assets',
    '  /fleet <17|18|19>                    parallel workspace orchestration across modules',
    '  /rules-check-drift [range]           advisory audit of CLAUDE.md/AGENTS.md/GEMINI.md drift',
    '',
    'Always establish the target Odoo version before doing version-sensitive work, and load the',
    'version-specific skills (odoo-17-coding-standard / odoo-18-coding-standard /',
    'odoo-19-coding-standard, odoo-17-dependency-context …) rather than assuming they are the same.',
    '',
    `Kit root: ${root}`,
    'Model discovery is available live through the odoo_* tools; official documentation is available',
    'offline through the odoo_kb_* tools for the configured versions.',
    '',
    'Non-negotiable rules:',
    '  - Never fetch, mount, copy, or modify Odoo Enterprise licensed source. Enter an Enterprise',
    '    dependency by technical name only.',
    '  - Route every module install/update/test through sandbox/bin/sandboxctl module (Docker Sandbox)',
    '    or `bash manage_modules.sh …` (local). Raw odoo-bin runs are blocked.',
    '  - Do not commit, push, merge, tag, or create releases without explicit user authorization.',
    '  - Keep secrets, customer data, and licensed source out of the repository and its artifacts.',
  ].join('\n')
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

/**
 * Register the kit into one preset scope.
 * @param ctx - the preset's standing scope context.
 * @param config - the row's config from `agent.cordis.yml`.
 */
export function apply(ctx, config) {
  const resolved = resolveConfig(config)

  // ── skills ────────────────────────────────────────────────────────────────
  const skills = ctx.get('skills')
  const skillsDir = resolved.repoRoot === undefined ? undefined : join(resolved.repoRoot, 'plugin', 'skills')
  if (skills !== undefined && skillsDir !== undefined) {
    void discoverSkills(skillsDir).then((found) => {
      for (const skill of found) {
        ctx.effect(() => skills.register({
          name: skill.name,
          description: skill.description,
          ...(skill.whenToUse === undefined ? {} : { whenToUse: skill.whenToUse }),
          content: skill.content,
          path: skill.path,
          resourceBase: { kind: 'directory', path: skill.directory },
          source: 'custom',
          metadata: { upstreamName: skill.upstreamName, kit: 'odoo-agent-pro-kit' },
        }), `odoo-agent-pro-kit.skill(${skill.name})`)
      }
      ctx.logger?.info?.(`odoo-agent-pro-kit: registered ${found.length} Odoo skills in kebab-case form`)
    }).catch((error) => {
      ctx.logger?.warn?.(`odoo-agent-pro-kit: skill registration failed: ${errorText(error)}`)
    })
  }

  // ── prompt section ────────────────────────────────────────────────────────
  // A static section is deliberate: `systemPrompt` context providers receive
  // only `{ scope, signal }`, so a per-session cwd is not available at
  // assembly time. Workspace detection is therefore surfaced through
  // `odoo_workspace_info` and through every tool's own version defaulting,
  // both of which do receive the calling agent's Session.
  ctx.effect(() => ctx.systemPrompt.section({
    name: 'odoo-agent-pro-kit:lifecycle',
    order: LIFECYCLE_SECTION_ORDER,
    text: lifecycleSectionText(resolved),
  }), 'odoo-agent-pro-kit.lifecycle-section')

  // ── lifecycle commands ────────────────────────────────────────────────────
  const commands = ctx.get('commands')
  const COMMANDS = [
    ['plan-analysis', 'plan-analysis.md', 'Odoo requirement analysis, model discovery, and PRD generation (17/18/19).'],
    ['start-coding', 'start-coding.md', 'Task-loop Odoo implementation with backend tests per task (17/18/19).'],
    ['testing', 'testing.md', 'Odoo frontend UI testing and documentation assets (17/18/19).'],
    ['fleet', 'fleet.md', 'Parallel Odoo workspace orchestration across modules (17/18/19).'],
    ['rules-check-drift', 'rules-check-drift.md', 'Advisory, read-only audit of CLAUDE.md/AGENTS.md/GEMINI.md drift.'],
  ]
  if (commands !== undefined) {
    for (const [commandName, file, description] of COMMANDS) {
      ctx.effect(() => commands.register({
        name: commandName,
        description,
        input: { hint: commandName === 'rules-check-drift' ? '[diff range, e.g. main...HEAD]' : '<17|18|19> [module_name]' },
        handler: async (invocation) => {
          try {
            const { version, rest } = parseVersionAndRest(invocation.rawInput)
            const body = await readCommandPrompt(resolved.repoRoot, file)
            if (body === undefined) {
              return {
                kind: 'error',
                text: `Odoo command "${commandName}" needs the kit repository: set repoRoot in the preset row `
                  + '(see integrations/deepseek/INSTALL.md).',
              }
            }
            const target = version ?? detectWorkspace(agentCwd(invocation.agent)).version
            const versionLine = target === undefined
              ? 'Ask the user for the Odoo version (17, 18, or 19) before proceeding.'
              : `Odoo version: ${target}.`
            const moduleLine = rest === '' ? '' : `Module/argument: ${rest}.`
            const prompt = [body, '', versionLine, moduleLine].filter(line => line !== '').join('\n')
            invocation.agent.followup(userMessage(prompt))
            return { kind: 'success', text: `Running /${commandName}${target === undefined ? '' : ` for Odoo ${target}`}.` }
          } catch (error) {
            return { kind: 'error', text: `/${commandName} failed: ${errorText(error)}` }
          }
        },
      }), `odoo-agent-pro-kit.command(${commandName})`)
    }
  }

  // ── live model discovery tools ────────────────────────────────────────────
  const versionParam = {
    type: 'string',
    description: 'Odoo version: 17.0, 18.0, or 19.0. Defaults to the configured/detected version.',
    enum: VERSIONS,
  }

  const registerTool = (definition) => {
    ctx.effect(() => ctx.tools.register(tool(definition)), `odoo-agent-pro-kit.tool(${definition.name})`)
  }

  registerTool({
    name: 'odoo_search_models',
    description: 'Search Odoo models of a connected database by technical or display name.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        query: { type: 'string', description: 'Search text, e.g. "sale.order" or "pricelist".' },
        version: versionParam,
        limit: { type: 'integer', description: 'Maximum results (default 20).' },
      },
      required: ['query'],
    },
    outputSchema: { type: 'array', items: { type: 'object', additionalProperties: true } },
    execute: async (args, exec) => {
      const version = pickVersion(args.version, resolved, agentCwd(exec?.agent))
      const limit = Number.isSafeInteger(args.limit) ? args.limit : 20
      const records = await executeKw(version, resolved, 'ir.model', 'search_read',
        [[['model', '=like', `%${args.query}%`]]],
        { fields: ['model', 'name', 'transient'], limit }, exec?.signal)
      return records.map(record => ({
        model: record.model,
        name: record.name,
        is_transient: record.transient === true,
      }))
    },
    render: value => jsonText(value),
  })

  registerTool({
    name: 'odoo_get_fields',
    description: 'List every field of one Odoo model, with type, required/readonly flags, and relation target.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        model_name: { type: 'string', description: 'Technical model name, e.g. sale.order.' },
        version: versionParam,
      },
      required: ['model_name'],
    },
    outputSchema: { type: 'object', additionalProperties: true },
    execute: async (args, exec) => {
      const version = pickVersion(args.version, resolved, agentCwd(exec?.agent))
      const fieldsGet = await executeKw(version, resolved, args.model_name, 'fields_get', [],
        { attributes: ['string', 'type', 'required', 'readonly', 'relation', 'help'] }, exec?.signal)
      return { model: args.model_name, version, fields: fieldList(fieldsGet) }
    },
    render: value => jsonText(value),
  })

  registerTool({
    name: 'odoo_get_relationships',
    description: 'List the relational fields (many2one, one2many, many2many) of one Odoo model.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        model_name: { type: 'string', description: 'Technical model name.' },
        version: versionParam,
      },
      required: ['model_name'],
    },
    outputSchema: { type: 'object', additionalProperties: true },
    execute: async (args, exec) => {
      const version = pickVersion(args.version, resolved, agentCwd(exec?.agent))
      const fieldsGet = await executeKw(version, resolved, args.model_name, 'fields_get', [],
        { attributes: ['string', 'type', 'relation', 'required'] }, exec?.signal)
      const relationships = fieldList(fieldsGet)
        .filter(field => field.type === 'many2one' || field.type === 'one2many' || field.type === 'many2many')
        .map(field => ({ name: field.name, type: field.type, relation: field.relation, string: field.string }))
      return { model: args.model_name, version, relationships }
    },
    render: value => jsonText(value),
  })

  registerTool({
    name: 'odoo_validate_field',
    description: 'Confirm whether one field exists on an Odoo model and return its exact definition.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        model_name: { type: 'string', description: 'Technical model name.' },
        field_name: { type: 'string', description: 'Technical field name.' },
        version: versionParam,
      },
      required: ['model_name', 'field_name'],
    },
    outputSchema: { type: 'object', additionalProperties: true },
    execute: async (args, exec) => {
      const version = pickVersion(args.version, resolved, agentCwd(exec?.agent))
      const fieldsGet = await executeKw(version, resolved, args.model_name, 'fields_get', [args.field_name],
        { attributes: ['string', 'type', 'required', 'readonly', 'relation', 'help'] }, exec?.signal)
      const [field] = fieldList(fieldsGet)
      if (field === undefined) {
        return { model: args.model_name, field: args.field_name, version, exists: false }
      }
      return { model: args.model_name, version, exists: true, field }
    },
    render: value => jsonText(value),
  })

  registerTool({
    name: 'odoo_get_model_info',
    description: 'Summarize one Odoo model: display name, transient flag, field and relational-field counts.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        model_name: { type: 'string', description: 'Technical model name.' },
        version: versionParam,
      },
      required: ['model_name'],
    },
    outputSchema: { type: 'object', additionalProperties: true },
    execute: async (args, exec) => {
      const version = pickVersion(args.version, resolved, agentCwd(exec?.agent))
      const records = await executeKw(version, resolved, 'ir.model', 'search_read',
        [[['model', '=', args.model_name]]], { fields: ['model', 'name', 'transient'], limit: 1 }, exec?.signal)
      const fieldsGet = await executeKw(version, resolved, args.model_name, 'fields_get', [],
        { attributes: ['string', 'type', 'relation'] }, exec?.signal)
      const fields = fieldList(fieldsGet)
      return {
        model: args.model_name,
        version,
        display_name: records[0]?.name,
        is_transient: records[0]?.transient === true,
        field_count: fields.length,
        relationship_count: fields.filter(field => field.type.endsWith('2many') || field.type === 'many2one').length,
      }
    },
    render: value => jsonText(value),
  })

  registerTool({
    name: 'odoo_list_all_models',
    description: 'List the models available on the connected Odoo database.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        limit: { type: 'integer', description: 'Maximum results (default 100).' },
        version: versionParam,
      },
      required: [],
    },
    outputSchema: { type: 'array', items: { type: 'object', additionalProperties: true } },
    execute: async (args, exec) => {
      const version = pickVersion(args.version, resolved, agentCwd(exec?.agent))
      const limit = Number.isSafeInteger(args.limit) ? args.limit : 100
      const records = await executeKw(version, resolved, 'ir.model', 'search_read', [],
        { fields: ['model', 'name'], limit, order: 'model' }, exec?.signal)
      return records.map(record => ({ model: record.model, name: record.name }))
    },
    render: value => jsonText(value),
  })

  registerTool({
    name: 'odoo_get_version_info',
    description: 'Report the connected Odoo version, server URL, database, user, and authentication state.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: { version: versionParam },
      required: [],
    },
    outputSchema: { type: 'object', additionalProperties: true },
    execute: async (args, exec) => {
      const version = pickVersion(args.version, resolved, agentCwd(exec?.agent))
      const spec = resolved.odoo[version] ?? {}
      if (!spec.url || !spec.db) {
        return { version, configured: false, hint: `Set ODOO${version.split('.')[0]}_URL and ODOO${version.split('.')[0]}_DB_NAME.` }
      }
      const session = await odooSession(version, resolved, exec?.signal)
      let serverVersion
      try {
        const info = await executeKw(version, resolved, 'ir.module.module', 'search_read',
          [[['name', '=', 'base']]], { fields: ['latest_version'], limit: 1 }, exec?.signal)
        serverVersion = info[0]?.latest_version
      } catch {
        serverVersion = undefined
      }
      return { version, configured: true, url: spec.url, database: spec.db, user: spec.user, uid: session.uid, server_version: serverVersion }
    },
    render: value => jsonText(value),
  })

  // ── workspace / configuration introspection ───────────────────────────────
  registerTool({
    name: 'odoo_workspace_info',
    description: 'Report the detected Odoo workspace: version, module, sandbox session, kit root, and configured knowledge bases and connections.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {},
      required: [],
    },
    outputSchema: { type: 'object', additionalProperties: true },
    execute: async (_args, exec) => {
      const cwd = agentCwd(exec?.agent)
      const detected = detectWorkspace(cwd)
      return {
        cwd,
        detected,
        default_version: resolved.defaultOdooVersion ?? detected.version ?? null,
        kit_root: resolved.repoRoot ?? null,
        knowledge_bases: Object.entries(resolved.knowledgeRoots)
          .map(([version, path]) => ({ version, path, exists: existsSync(path) })),
        connections: VERSIONS.map((version) => ({
          version,
          url: resolved.odoo[version]?.url ?? null,
          database: resolved.odoo[version]?.db ?? null,
          user: resolved.odoo[version]?.user ?? null,
          credentials_present: Boolean(resolved.odoo[version]?.url && resolved.odoo[version]?.db),
        })),
        guard: {
          allow_raw_odoo: resolved.allowRawOdoo,
          allow_vcs_write_env: resolved.allowVcsWriteEnv,
          vcs_authorized_marker: vcsMarkerPresent(cwd),
          vcs_writes_allowed: vcsWritesAllowed(resolved, exec?.agent),
        },
      }
    },
    render: value => jsonText(value),
  })

  // ── offline knowledge-base tools ──────────────────────────────────────────
  registerTool({
    name: 'odoo_kb_search',
    description: 'Search the per-version Odoo official documentation knowledge base (OKF bundle) and return ranked pages with snippets.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        query: { type: 'string', description: 'Search terms, e.g. "compute field depends".' },
        version: versionParam,
        limit: { type: 'integer', description: 'Maximum results (default 8).' },
      },
      required: ['query'],
    },
    outputSchema: { type: 'array', items: { type: 'object', additionalProperties: true } },
    execute: async (args, exec) => {
      const version = VERSION_ALIASES[String(args.version ?? '')] ?? args.version ?? pickVersion(undefined, resolved, undefined)
      const root = kbRoot(version, resolved)
      const terms = String(args.query).toLowerCase().split(/\s+/).filter(term => term.length > 1)
      if (terms.length === 0) throw new Error('Provide at least one search term of two or more characters.')
      const limit = Number.isSafeInteger(args.limit) ? args.limit : 8
      const scored = []
      for (const file of await kbMarkdownFiles(root)) {
        exec?.signal?.throwIfAborted?.()
        let raw
        try {
          raw = await readFile(file, 'utf8')
        } catch {
          continue
        }
        const result = kbScore(raw, terms)
        if (result === 0) continue
        scored.push({
          path: relative(root, file),
          title: kbTitle(raw, basename(file)),
          score: result.score,
          snippet: result.snippet,
        })
      }
      scored.sort((left, right) => right.score - left.score || left.path.localeCompare(right.path))
      return scored.slice(0, limit).map(({ path, title, score, snippet }) => ({ path, title, score, snippet }))
    },
    render: value => jsonText(value),
  })

  registerTool({
    name: 'odoo_kb_read',
    description: 'Read one page of the per-version Odoo official documentation knowledge base by relative path.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        path: { type: 'string', description: 'Page path relative to the bundle root, e.g. developer/reference/backend/orm.md.' },
        version: versionParam,
        max_chars: { type: 'integer', description: 'Maximum characters to return (default 24000).' },
      },
      required: ['path'],
    },
    outputSchema: { type: 'object', additionalProperties: true },
    execute: async (args) => {
      const version = VERSION_ALIASES[String(args.version ?? '')] ?? args.version ?? pickOptionalVersion(resolved)
      const root = kbRoot(version, resolved)
      const target = safeKbPath(root, args.path)
      if (!existsSync(target)) throw new Error(`No such knowledge-base page for Odoo ${version}: ${args.path}`)
      const raw = await readFile(target, 'utf8')
      const maxChars = Number.isSafeInteger(args.max_chars) ? args.max_chars : 24000
      return {
        version,
        path: relative(root, target),
        title: kbTitle(raw, basename(target)),
        truncated: raw.length > maxChars,
        content: raw.length > maxChars ? `${raw.slice(0, maxChars)}\n\n… truncated …` : raw,
      }
    },
    render: value => jsonText(value),
  })

  registerTool({
    name: 'odoo_kb_list',
    description: 'List the configured Odoo documentation knowledge bases, or the pages inside one of them.',
    parameters: {
      type: 'object',
      additionalProperties: false,
      properties: {
        version: versionParam,
        path: { type: 'string', description: 'Directory path relative to the bundle root; omit to list configured bundles.' },
      },
      required: [],
    },
    outputSchema: { type: 'object', additionalProperties: true },
    execute: async (args) => {
      if (args.version === undefined && args.path === undefined) {
        return {
          bundles: Object.entries(resolved.knowledgeRoots).map(([version, path]) => ({ version, path, exists: existsSync(path) })),
        }
      }
      const version = VERSION_ALIASES[String(args.version ?? '')] ?? args.version ?? pickOptionalVersion(resolved)
      const root = kbRoot(version, resolved)
      const target = safeKbPath(root, args.path)
      if (!existsSync(target)) throw new Error(`No such knowledge-base directory for Odoo ${version}: ${args.path ?? '.'}`)
      const entries = await readdir(target, { withFileTypes: true })
      return {
        version,
        path: relative(root, target) || '.',
        entries: entries
          .filter(entry => !entry.name.startsWith('.'))
          .map(entry => ({ name: entry.name, type: entry.isDirectory() ? 'directory' : 'file' }))
          .sort((left, right) => left.name.localeCompare(right.name)),
      }
    },
    render: value => jsonText(value),
  })

  // ── guard ────────────────────────────────────────────────────────────────
  ctx.effect(() => ctx.tools.guard(execution => guardReason(execution, resolved)), 'odoo-agent-pro-kit.guard')

  ctx.logger?.info?.('odoo-agent-pro-kit: Odoo 17/18/19 lifecycle, skills, commands, model discovery, and knowledge base ready')
}

/** Default knowledge-base version when a call names none. */
function pickOptionalVersion(config) {
  return config.defaultOdooVersion ?? VERSIONS.find(version => config.knowledgeRoots[version] !== undefined) ?? '19.0'
}

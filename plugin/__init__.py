"""
odoo-agent-pro-kit — native Hermes plugin registration.

Wires the existing plugin/odoo_mcp/ package (config, connection pooling,
model discovery — the same code the standalone MCP server at
odoo_mcp/odoo_mcp_server.py uses) directly into Hermes as in-process tools,
so no separate MCP process/port/sidecar is required for a Hermes session.
Also registers the five odoo_commanding_system slash commands, session-start
Odoo workspace detection, and every bundled skill under skills/.

This coexists with the Claude-Code-style manifest at
.claude-plugin/plugin.json — that one is read when this plugin/ directory is
installed as a Claude Code plugin; this file is read when it's installed via
`hermes plugins install owner/repo/plugin`.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_PLUGIN_DIR = Path(__file__).parent

# One OdooMcpServer-equivalent connection per Odoo version, created lazily and
# reused for the life of the process (mirrors the standalone MCP server's
# module-level singleton pattern in odoo_mcp/odoo_mcp_server.py).
_discovery_by_version: Dict[str, Any] = {}


def _get_discovery(version: Optional[str]):
    """Get (or lazily create) a ModelDiscovery for the given Odoo version.

    Reuses plugin/odoo_mcp/{config,connection_manager,model_extractor}.py
    unchanged — same connection pooling, retry logic, and XML-RPC /
    JSON-RPC-2.0 protocol selection as the standalone MCP server.
    """
    from .odoo_mcp.config import load_config
    from .odoo_mcp.connection_manager import ConnectionManager
    from .odoo_mcp.model_extractor import ModelDiscovery

    config = load_config(version)
    key = config.odoo_version or "default"
    cached = _discovery_by_version.get(key)
    if cached is not None:
        return cached, config

    manager = ConnectionManager(config)
    if not manager.initialize():
        raise RuntimeError(
            f"Failed to connect to Odoo {config.odoo_version} at "
            f"{config.get_base_url()} (db={config.database}). Check "
            f"ODOO_URL/ODOO_DB_NAME/ODOO_DB_USER/ODOO_DB_PASSWORD (or the "
            f"version-prefixed ODOO17_*/ODOO18_*/ODOO19_* overrides)."
        )
    client = manager.get_connection()
    if client is None:
        raise RuntimeError(f"Failed to obtain an authenticated Odoo {config.odoo_version} connection")

    discovery = ModelDiscovery(client)
    _discovery_by_version[key] = (discovery, manager)
    return (discovery, manager), config


def _close_all_connections() -> None:
    """Close every pooled connection opened this session (on_session_end)."""
    for _key, entry in list(_discovery_by_version.items()):
        try:
            _discovery, manager = entry
            manager.close_all()
        except Exception as exc:  # noqa: BLE001 - never let cleanup crash the hook
            logger.warning("odoo-agent-pro-kit: error closing connection: %s", exc)
    _discovery_by_version.clear()


def _err(message: str) -> str:
    return json.dumps({"error": message})


# ---------------------------------------------------------------------------
# Tool handlers — mirror odoo_mcp/odoo_mcp_server.py's @mcp.tool() functions
# one-for-one, but called in-process (no stdio/SSE MCP transport needed).
# ---------------------------------------------------------------------------


def _tool_search_models(args: dict, **_kwargs) -> str:
    version = args.get("version")
    query = args.get("query", "")
    limit = int(args.get("limit", 20))
    try:
        (discovery, _manager), _config = _get_discovery(version)
    except RuntimeError as exc:
        return _err(str(exc))
    models = discovery.search_models(query, limit=limit)
    return json.dumps(
        [{"model": m.model, "name": m.name, "module": m.module, "is_transient": m.is_transient} for m in models],
        indent=2,
    )


def _tool_get_fields(args: dict, **_kwargs) -> str:
    version = args.get("version")
    model_name = args.get("model_name", "")
    try:
        (discovery, _manager), _config = _get_discovery(version)
    except RuntimeError as exc:
        return _err(str(exc))
    context = discovery.get_model(model_name)
    if not context:
        return _err(f"Model not found: {model_name}")
    return json.dumps(
        {
            "model": context.model.model,
            "name": context.model.name,
            "fields": [
                {
                    "name": f.name,
                    "type": f.field_type,
                    "string": f.string,
                    "required": f.required,
                    "readonly": f.readonly,
                    "relation": f.relation,
                    "help": f.help,
                }
                for f in context.fields
            ],
        },
        indent=2,
    )


def _tool_get_relationships(args: dict, **_kwargs) -> str:
    version = args.get("version")
    model_name = args.get("model_name", "")
    try:
        (discovery, _manager), _config = _get_discovery(version)
    except RuntimeError as exc:
        return _err(str(exc))
    context = discovery.get_model(model_name)
    if not context:
        return _err(f"Model not found: {model_name}")
    return json.dumps(
        {
            "model": context.model.model,
            "relationships": [
                {"name": r.name, "type": r.type, "relation": r.relation, "inverse_name": r.inverse_name}
                for r in context.relationships
            ],
        },
        indent=2,
    )


def _tool_validate_field(args: dict, **_kwargs) -> str:
    version = args.get("version")
    model_name = args.get("model_name", "")
    field_name = args.get("field_name", "")
    expected_type = args.get("expected_type")
    try:
        (discovery, _manager), _config = _get_discovery(version)
    except RuntimeError as exc:
        return _err(str(exc))
    context = discovery.get_model(model_name)
    if not context:
        return _err(f"Model not found: {model_name}")

    field = next((f for f in context.fields if f.name == field_name), None)
    if not field:
        return json.dumps(
            {
                "valid": False,
                "reason": f"Field '{field_name}' not found in model '{model_name}'",
                "available_fields": [f.name for f in context.fields[:10]],
            },
            indent=2,
        )
    if expected_type and field.field_type != expected_type:
        return json.dumps(
            {
                "valid": False,
                "reason": f"Field '{field_name}' has type '{field.field_type}', expected '{expected_type}'",
                "field_type": field.field_type,
            },
            indent=2,
        )
    return json.dumps(
        {
            "valid": True,
            "field_name": field.name,
            "field_type": field.field_type,
            "string": field.string,
            "required": field.required,
            "readonly": field.readonly,
            "relation": field.relation,
        },
        indent=2,
    )


def _tool_get_model_info(args: dict, **_kwargs) -> str:
    version = args.get("version")
    model_name = args.get("model_name", "")
    try:
        (discovery, _manager), _config = _get_discovery(version)
    except RuntimeError as exc:
        return _err(str(exc))
    context = discovery.get_model(model_name)
    if not context:
        return _err(f"Model not found: {model_name}")
    return json.dumps(
        {
            "model": context.model.model,
            "name": context.model.name,
            "description": context.model.description,
            "is_transient": context.model.is_transient,
            "module": context.model.module,
            "field_count": len(context.fields),
            "relationship_count": len(context.relationships),
        },
        indent=2,
    )


def _tool_list_all_models(args: dict, **_kwargs) -> str:
    version = args.get("version")
    limit = int(args.get("limit", 100))
    try:
        (discovery, _manager), _config = _get_discovery(version)
    except RuntimeError as exc:
        return _err(str(exc))
    models = discovery.list_models(limit=limit)
    return json.dumps(
        [{"model": m.model, "name": m.name, "module": m.module, "is_transient": m.is_transient} for m in models],
        indent=2,
    )


def _tool_get_version_info(args: dict, **_kwargs) -> str:
    version = args.get("version")
    try:
        (_discovery, _manager), config = _get_discovery(version)
    except RuntimeError as exc:
        return _err(str(exc))
    return json.dumps(
        {
            "odoo_version": config.odoo_version,
            "protocol": config.protocol,
            "host": config.host,
            "port": config.port,
            "database": config.database,
            "username": config.username,
            "status": "connected",
        },
        indent=2,
    )


_VERSION_PARAM = {
    "type": "string",
    "description": "Odoo version, e.g. '17.0'/'18.0'/'19.0' (also accepts '17'/'18'/'19'). "
    "Omit to use DEFAULT_ODOO_VERSION / the active sandbox session / 19.0.",
}

_TOOLS = [
    (
        "odoo_search_models",
        _tool_search_models,
        {
            "name": "odoo_search_models",
            "description": "Search Odoo models by name or description over a live Odoo 17/18/19 connection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string."},
                    "limit": {"type": "integer", "description": "Maximum number of results (default 20)."},
                    "version": _VERSION_PARAM,
                },
                "required": ["query"],
            },
        },
    ),
    (
        "odoo_get_fields",
        _tool_get_fields,
        {
            "name": "odoo_get_fields",
            "description": "Get all field definitions for an Odoo model (e.g. 'res.partner').",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "Technical model name, e.g. 'res.partner'."},
                    "version": _VERSION_PARAM,
                },
                "required": ["model_name"],
            },
        },
    ),
    (
        "odoo_get_relationships",
        _tool_get_relationships,
        {
            "name": "odoo_get_relationships",
            "description": "Get the relationship map (many2one/one2many/many2many) for an Odoo model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "Technical model name, e.g. 'res.partner'."},
                    "version": _VERSION_PARAM,
                },
                "required": ["model_name"],
            },
        },
    ),
    (
        "odoo_validate_field",
        _tool_validate_field,
        {
            "name": "odoo_validate_field",
            "description": "Validate that a field exists on an Odoo model, optionally checking its type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "Technical model name."},
                    "field_name": {"type": "string", "description": "Field name to validate."},
                    "expected_type": {"type": "string", "description": "Optional expected field type, e.g. 'many2one'."},
                    "version": _VERSION_PARAM,
                },
                "required": ["model_name", "field_name"],
            },
        },
    ),
    (
        "odoo_get_model_info",
        _tool_get_model_info,
        {
            "name": "odoo_get_model_info",
            "description": "Get summary information (description, field/relationship counts) about an Odoo model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "Technical model name."},
                    "version": _VERSION_PARAM,
                },
                "required": ["model_name"],
            },
        },
    ),
    (
        "odoo_list_all_models",
        _tool_list_all_models,
        {
            "name": "odoo_list_all_models",
            "description": "List all available Odoo models on the connected database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of results (default 100)."},
                    "version": _VERSION_PARAM,
                },
                "required": [],
            },
        },
    ),
    (
        "odoo_get_version_info",
        _tool_get_version_info,
        {
            "name": "odoo_get_version_info",
            "description": "Get the connected Odoo version, protocol (XML-RPC/JSON-RPC-2.0), host, and database info.",
            "parameters": {"type": "object", "properties": {"version": _VERSION_PARAM}, "required": []},
        },
    ),
]


# ---------------------------------------------------------------------------
# Slash commands — /plan-analysis, /start-coding, /testing, /fleet, /rules-check-drift
# ---------------------------------------------------------------------------

_VALID_VERSIONS = {"17", "18", "19"}


def _parse_version_and_rest(raw_args: str) -> tuple[Optional[str], str]:
    parts = raw_args.strip().split(None, 1)
    if parts and parts[0] in _VALID_VERSIONS:
        return parts[0], (parts[1] if len(parts) > 1 else "")
    return None, raw_args.strip()


def _command_prompt(
    command_md_relpath: str,
    version: Optional[str],
    rest: str,
    extra: str,
    version_optional: bool = False,
) -> str:
    body = (_PLUGIN_DIR / command_md_relpath).read_text(encoding="utf-8")
    # Strip the YAML frontmatter (--- ... ---) the same way the Claude Code
    # command loader does; the remaining body is the actual instruction text.
    if body.startswith("---"):
        end = body.find("---", 3)
        if end != -1:
            body = body[end + 3 :].lstrip("\n")
    if version:
        version_line = f"Odoo version: {version}."
    elif version_optional:
        version_line = ""
    else:
        version_line = "Ask the user for the Odoo version (17, 18, or 19) before proceeding."
    module_line = f"Module/argument: {rest}." if rest else ""
    return f"{body}\n\n{version_line} {module_line}\n{extra}".strip()


def _make_command_handler(ctx, command_md_relpath: str, extra: str = "", version_optional: bool = False):
    def _handler(raw_args: str) -> str:
        version, rest = _parse_version_and_rest(raw_args)
        try:
            from .hooks.checks.hermes_adapter import command_gate

            cmd_name = command_md_relpath.split("/")[-1].removesuffix(".md")
            block = command_gate(cmd_name, raw_args, Path.cwd())
            if block:
                return block
        except Exception as exc:  # noqa: BLE001 - a gate failure must never break the command
            logger.debug("[odoo-agent-pro-kit] command_gate failed: %s", exc)
        prompt = _command_prompt(command_md_relpath, version, rest, extra, version_optional)
        queued = ctx.inject_message(prompt, role="user")
        if queued:
            return None
        return prompt

    return _handler


# ---------------------------------------------------------------------------
# Hooks — session-start Odoo workspace detection, session-end connection cleanup
# ---------------------------------------------------------------------------

_MCP_PORTS = {"17.0": 8765, "18.0": 8766, "19.0": 8767}


def _on_session_start(**_kwargs) -> None:
    import os

    session_file = Path(os.environ.get("SANDBOX_SESSION_FILE", "./.sandbox/session.json"))
    if session_file.is_file():
        try:
            data = json.loads(session_file.read_text())
            runtime = data.get("runtime", {})
            logger.info(
                "[odoo-agent-pro-kit] Sandbox session %s — Odoo %s, module %s, status %s, "
                "Compose project %s, Odoo target http://odoo:8069",
                data.get("session_id"),
                data.get("odoo_version"),
                data.get("module"),
                data.get("status"),
                runtime.get("compose_project", "unknown"),
            )
        except (OSError, ValueError, KeyError) as exc:
            logger.debug("[odoo-agent-pro-kit] Could not parse sandbox session file: %s", exc)
        return

    for version in ("19.0", "18.0", "17.0"):
        if Path(f"./{version}").is_dir():
            logger.info(
                "[odoo-agent-pro-kit] Detected Odoo %s workspace in %s — odoo_* tools default to this version",
                version,
                Path.cwd(),
            )
            break

    try:
        from .hooks.checks.hermes_adapter import session_start_lines

        for line in session_start_lines(Path.cwd()):
            logger.info("[odoo-agent-pro-kit] %s", line)
    except Exception as exc:  # noqa: BLE001 - session-start detail must never crash the hook
        logger.debug("[odoo-agent-pro-kit] session_start_lines failed: %s", exc)


def _on_session_end(**_kwargs) -> None:
    _close_all_connections()


# ---------------------------------------------------------------------------
# register(ctx) — the single Hermes entrypoint
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    # --- odoo_* tools: in-process equivalents of odoo_mcp_server.py ---
    for name, handler, schema in _TOOLS:
        ctx.register_tool(name=name, toolset="odoo_mcp", schema=schema, handler=handler)

    # --- slash commands: /plan-analysis, /start-coding, /testing, /fleet, /rules-check-drift ---
    ctx.register_command(
        "plan-analysis",
        _make_command_handler(
            ctx,
            "commands/plan-analysis.md",
            extra="Use the odoo-agent-pro-kit:odoo_commanding_system skill (skill_view) "
            "instead of a bare Skill-tool reference, and prefer the odoo_search_models / "
            "odoo_get_fields / odoo_get_relationships / odoo_validate_field tools over a "
            "separate MCP server process for model discovery.",
        ),
        description="Odoo requirement analysis, model discovery, and PRD generation for Odoo 17/18/19.",
        args_hint="<17|18|19> [module_name]",
    )
    ctx.register_command(
        "start-coding",
        _make_command_handler(
            ctx,
            "commands/start-coding.md",
            extra="Use the odoo-agent-pro-kit:odoo_commanding_system skill (skill_view).",
        ),
        description="Task-loop implementation with backend tests per task, for Odoo 17/18/19.",
        args_hint="<17|18|19> [module_name]",
    )
    ctx.register_command(
        "testing",
        _make_command_handler(
            ctx,
            "commands/testing.md",
            extra="Use the odoo-agent-pro-kit:odoo_commanding_system skill (skill_view).",
        ),
        description="Frontend UI tests plus documentation assets for Odoo 17/18/19.",
        args_hint="<17|18|19> [module_name]",
    )
    ctx.register_command(
        "fleet",
        _make_command_handler(
            ctx,
            "commands/fleet.md",
            extra="Use the odoo-agent-pro-kit:odoo_commanding_system skill (skill_view).",
        ),
        description="Parallel workspace orchestration across multiple Odoo modules for Odoo 17/18/19.",
        args_hint="<17|18|19>",
    )
    ctx.register_command(
        "rules-check-drift",
        _make_command_handler(
            ctx,
            "commands/rules-check-drift.md",
            extra="Use the odoo-agent-pro-kit:odoo_rules_drift_check skill (skill_view), and "
            "prefer the odoo_search_models / odoo_get_fields / odoo_validate_field / "
            "odoo_get_relationships tools for Tier 2 confirmation instead of a separate MCP "
            "server process. Skip Tier 2 silently when no connection is available.",
            version_optional=True,
        ),
        description="Audit CLAUDE.md/AGENTS.md/GEMINI.md against recent changes and PRD gate state. Advisory, read-only.",
        args_hint="[diff range, e.g. main...HEAD]",
    )

    # --- hooks: session-start Odoo workspace detection, session-end cleanup ---
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("on_session_end", _on_session_end)

    # --- dynamic context-usage handoff guard (Phase 8) ---
    # Fires on every real per-turn token-usage report (post_api_request),
    # regardless of which command/step is running, and regardless of module
    # complexity — see plugin/context_guard.py for the threshold logic.
    try:
        from .context_guard import maybe_handle_context_pressure

        def _on_post_api_request(**kwargs: Any) -> None:
            maybe_handle_context_pressure(ctx, **kwargs)

        ctx.register_hook("post_api_request", _on_post_api_request)
    except Exception as exc:  # noqa: BLE001 - never block plugin registration
        logger.warning("odoo-agent-pro-kit: context_guard hook registration failed: %s", exc)

    # --- Hermes tool-call parity with the Claude Code hooks (Task 11) ---
    # pre_tool_call CAN block (guard/paths violations); post_tool_call is
    # observe-only (odoo_lint findings + sandbox operation-result checks are
    # surfaced as warnings). See plugin/hooks/checks/hermes_adapter.py.
    try:
        from .hooks.checks.hermes_adapter import post_tool_call_notes, pre_tool_call_directive

        def _pre_tool_call(**kwargs: Any):
            try:
                return pre_tool_call_directive(
                    kwargs.get("tool_name", ""),
                    kwargs.get("args") or kwargs.get("tool_args") or kwargs.get("arguments") or {},
                    Path.cwd(),
                )
            except Exception as exc:  # noqa: BLE001 - hooks must never break a turn
                logger.debug("[odoo-agent-pro-kit] pre_tool_call hook failed: %s", exc)
                return None

        def _post_tool_call(**kwargs: Any) -> None:
            try:
                for note in post_tool_call_notes(
                    kwargs.get("tool_name", ""),
                    kwargs.get("args") or kwargs.get("tool_args") or kwargs.get("arguments") or {},
                    Path.cwd(),
                ):
                    logger.warning("[odoo-agent-pro-kit] %s", note)
            except Exception as exc:  # noqa: BLE001 - hooks must never break a turn
                logger.debug("[odoo-agent-pro-kit] post_tool_call hook failed: %s", exc)

        ctx.register_hook("pre_tool_call", _pre_tool_call)
        ctx.register_hook("post_tool_call", _post_tool_call)
    except Exception as exc:  # noqa: BLE001 - never block plugin registration
        logger.warning("odoo-agent-pro-kit: tool-call hook registration failed: %s", exc)

    # --- bundled skills: every plugin/skills/<name>/SKILL.md ---
    skills_dir = _PLUGIN_DIR / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                ctx.register_skill(child.name, skill_md)

    logger.info(
        "odoo-agent-pro-kit: registered %d odoo_* tools, 5 slash commands, 5 hooks, and skills from %s",
        len(_TOOLS),
        skills_dir,
    )

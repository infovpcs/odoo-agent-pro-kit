"""
Odoo MCP Client Module

Provides a client wrapper for the Odoo MCP server.
This is used by the copilot agent to query live Odoo data.
"""

import logging
import json
import time
import asyncio
import requests
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from .config import OdooConfig, load_config
from mcp import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    data: Any
    expires_at: float


class OdooMcpClient:
    """
    Client for Odoo MCP Server.

    Provides convenient methods to query live Odoo data through MCP.
    Includes caching to reduce server calls with lazy connection initialization.
    """

    def __init__(
        self,
        config: Optional[OdooConfig] = None,
        cache_ttl: int = 3600
    ):
        """
        Initialize Odoo MCP client.

        Args:
            config: Odoo configuration. If None, loads from environment.
            cache_ttl: Cache time-to-live in seconds (default: 1 hour).
        """
        self.config = config or load_config()
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, CacheEntry] = {}
        
        # MCP session state
        self._session: Optional[ClientSession] = None
        self._client_context = None
        self._initialized = False
        self._lock = asyncio.Lock()

        # MCP server connection settings from config
        self.mcp_host = self.config.mcp_server_host
        self.mcp_port = self.config.mcp_server_port
        self.request_timeout = max(5, int(self.config.request_timeout))
        self.trace = os.environ.get("MCP_TRACE", "false").lower() == "true"

    async def _call_tool_with_timeout(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call MCP tool with timeout to avoid hanging SSE streams."""
        if not self._session:
            return None
        if self.trace:
            logger.info("MCP TRACE call start: tool=%s params=%s", tool_name, params)
        return await asyncio.wait_for(
            self._session.call_tool(tool_name, params),
            timeout=self.request_timeout,
        )

    @staticmethod
    def _parse_tool_content(result: Any) -> Any:
        """Parse FastMCP tool result content safely."""
        if not (hasattr(result, "content") and result.content):
            return None
        content = result.content[0]
        if hasattr(content, "text"):
            return json.loads(content.text)
        if isinstance(content, dict):
            return json.loads(content.get("text", "{}"))
        return None

    async def _ensure_session(self, force_reconnect: bool = False):
        """Ensure MCP session is initialized (Lazy Loading).

        Args:
            force_reconnect: If True, force reconnection even if already initialized.
        """
        # If forcing reconnect, reset state first
        if force_reconnect and self._session:
            await self.disconnect()

        if self._initialized and self._session and not force_reconnect:
            return

        async with self._lock:
            # Double-check after acquiring lock
            if self._initialized and self._session and not force_reconnect:
                return

            try:
                # Use SSE transport for network-connected server
                # Construct SSE URL from host and port
                sse_url = f"http://{self.mcp_host}:{self.mcp_port}/sse"
                logger.info(f"Connecting to Odoo MCP Server at {sse_url}...")

                # Preflight check to avoid entering SSE context when endpoint is not healthy.
                preflight = requests.get(sse_url, timeout=3, stream=True)
                ctype = preflight.headers.get("content-type", "")
                preflight_ok = preflight.status_code == 200 and "text/event-stream" in ctype
                preflight.close()
                if not preflight_ok:
                    logger.warning(
                        "MCP preflight failed for %s (status=%s, content-type=%s)",
                        sse_url,
                        preflight.status_code,
                        ctype,
                    )
                    self._initialized = False
                    self._session = None
                    self._client_context = None
                    return

                self._client_context = sse_client(sse_url)
                # Wrap SSE connection with timeout to avoid hanging
                try:
                    read, write = await asyncio.wait_for(
                        self._client_context.__aenter__(),
                        timeout=self.request_timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(f"SSE connection timeout after {self.request_timeout}s")
                    self._initialized = False
                    self._session = None
                    self._client_context = None
                    return

                self._session = ClientSession(read, write)
                await asyncio.wait_for(
                    self._session.initialize(),
                    timeout=self.request_timeout
                )

                self._initialized = True
                logger.info("✅ Odoo MCP Session initialized successfully")
            except BaseException as e:
                logger.exception("❌ Failed to initialize Odoo MCP Session")
                # Ensure partially-opened async contexts are closed in the same task.
                try:
                    if self._session:
                        try:
                            await self._session.__aexit__(None, None, None)
                        except BaseException:
                            pass
                        self._session = None
                    if self._client_context:
                        try:
                            await self._client_context.__aexit__(None, None, None)
                        except BaseException:
                            pass
                        self._client_context = None
                except BaseException:
                    pass
                self._initialized = False
                self._session = None
                # Don't raise, fallback methods will handle missing session

    async def disconnect(self):
        """Close the MCP session."""
        async with self._lock:
            if self._session:
                try:
                    await self._session.__aexit__(None, None, None)
                except BaseException as e:
                    logger.debug(f"Ignoring MCP session close error: {e}")
                self._session = None
            if self._client_context:
                try:
                    await self._client_context.__aexit__(None, None, None)
                except BaseException as e:
                    logger.debug(f"Ignoring MCP client context close error: {e}")
                self._client_context = None
            self._initialized = False
            logger.info("Odoo MCP Session closed")

    def _get_cache_key(self, method: str, *args, **kwargs) -> str:
        """Generate cache key for a method call."""
        key_parts = [method] + [str(a) for a in args]
        key_parts += [f"{k}={v}" for k, v in sorted(kwargs.items())]
        return ":".join(key_parts)

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry.expires_at:
                logger.debug(f"Cache hit: {key}")
                return entry.data
            else:
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        """Set cached result with TTL."""
        self._cache[key] = CacheEntry(
            data=data,
            expires_at=time.time() + self.cache_ttl
        )
        logger.debug(f"Cached: {key}")

    def _log_trace_result(self, tool_name: str, payload: Any, started_at: float) -> None:
        """Emit concise trace line for MCP tool result."""
        if not self.trace:
            return
        elapsed_ms = int((time.time() - started_at) * 1000)
        try:
            if isinstance(payload, dict):
                if "fields" in payload and isinstance(payload.get("fields"), list):
                    logger.info("MCP TRACE call done: tool=%s fields=%s took=%sms", tool_name, len(payload["fields"]), elapsed_ms)
                    return
                if "models" in payload and isinstance(payload.get("models"), list):
                    logger.info("MCP TRACE call done: tool=%s models=%s took=%sms", tool_name, len(payload["models"]), elapsed_ms)
                    return
                if "relationships" in payload and isinstance(payload.get("relationships"), list):
                    logger.info("MCP TRACE call done: tool=%s relationships=%s took=%sms", tool_name, len(payload["relationships"]), elapsed_ms)
                    return
            logger.info("MCP TRACE call done: tool=%s type=%s took=%sms", tool_name, type(payload).__name__, elapsed_ms)
        except Exception:
            logger.info("MCP TRACE call done: tool=%s took=%sms", tool_name, elapsed_ms)

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Cache cleared")

    def update_config(self, config: "OdooConfig") -> None:
        """Update config and force reconnection on next call.

        Args:
            config: New Odoo configuration (may have different port).
        """
        # Disconnect existing session if config changed
        if self._session:
            logger.info(f"Config changed, disconnecting old session")
            # Schedule async disconnect without blocking
            asyncio.create_task(self.disconnect())

        self.config = config
        self.mcp_host = config.mcp_server_host
        self.mcp_port = config.mcp_server_port
        logger.info(f"Updated MCP client config: {self.mcp_host}:{self.mcp_port}")

    def is_connected(self) -> bool:
        """Check if MCP session is connected."""
        return self._initialized and self._session is not None

    async def check_connection(self) -> bool:
        """Check and verify connection is working."""
        if not self.is_connected():
            return False

        try:
            # Try a simple call to verify connection
            await asyncio.wait_for(self._session.list_tools(), timeout=self.request_timeout)
            return True
        except Exception as e:
            logger.warning(f"Connection check failed: {e}")
            self._initialized = False
            self._session = None
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        expired = sum(1 for e in self._cache.values() if now >= e.expires_at)
        return {
            "total_entries": len(self._cache),
            "expired_entries": expired,
            "active_entries": len(self._cache) - expired,
            "cache_ttl": self.cache_ttl
        }

    # ==========================================
    # MCP Tool Methods (simulated - use MCP server)
    # ==========================================

    async def search_models(
        self,
        query: str,
        limit: int = 20,
        use_cache: bool = True,
        force_reconnect: bool = False
    ) -> Dict[str, Any]:
        """
        Search Odoo models by name or description.

        Args:
            query: Search query string.
            limit: Maximum results.
            use_cache: Use cached result if available.
            force_reconnect: Force reconnection to MCP server (useful after version switch).

        Returns:
            Dict of matching models.
        """
        cache_key = self._get_cache_key("search_models", query, limit)
        if use_cache and not force_reconnect:
            cached = self._get_cache(cache_key)
            if cached:
                return cached

        # Try direct discovery if available
        if hasattr(self, 'discovery') and self.discovery:
            started = time.time()
            try:
                models = self.discovery.search_models(query, limit=limit)
                response = {
                    "source": "live_odoo",
                    "query": query,
                    "models": [
                        {
                            "model": m.model,
                            "name": m.name,
                            "module": m.module,
                            "description": m.description,
                            "is_transient": m.is_transient
                        }
                        for m in models
                    ]
                }
                self._set_cache(cache_key, response)
                self._log_trace_result("search_models", response, started)
                return response
            except Exception as e:
                logger.warning(f"Direct discovery search_models failed: {e}. Using fallback.")

        # Static fallback if MCP fails or not connected
        result = {
            "source": "static_fallback",
            "query": query,
            "models": [
                {"model": "res.partner", "name": "Contact", "module": "base"},
                {"model": "res.users", "name": "User", "module": "base"},
                {"model": "sale.order", "name": "Sale Order", "module": "sale"},
            ],
            "note": "MCP server not connected or failed - using static fallback"
        }
        
        if use_cache:
            self._set_cache(cache_key, result)
            
        return result

    async def get_fields(
        self,
        model_name: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get all fields for a model.

        Args:
            model_name: Technical model name.
            use_cache: Use cached result if available.

        Returns:
            Dict of field definitions.
        """
        cache_key = self._get_cache_key("get_fields", model_name)
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                return cached

        # Try direct discovery if available
        if hasattr(self, 'discovery') and self.discovery:
            started = time.time()
            try:
                context = self.discovery.get_model(model_name)
                if context:
                    res_data = {
                        "source": "live_odoo",
                        "model": model_name,
                        "fields": [
                            {
                                "name": f.name,
                                "type": f.field_type,
                                "string": f.string,
                                "required": f.required,
                                "readonly": f.readonly,
                                "relation": f.relation,
                                "help": f.help
                            }
                            for f in context.fields
                        ]
                    }
                    self._set_cache(cache_key, res_data)
                    self._log_trace_result("get_fields", res_data, started)
                    return res_data
            except Exception as e:
                logger.warning(f"Direct discovery get_fields failed: {e}. Using fallback.")

        # Static fallback if MCP fails or not connected
        result = {
            "source": "static_fallback",
            "model": model_name,
            "fields": [
                {"name": "id", "type": "integer", "string": "ID", "required": True},
                {"name": "name", "type": "char", "string": "Name", "required": True},
            ],
            "note": "MCP server not connected or failed - using static fallback"
        }

        if use_cache:
            self._set_cache(cache_key, result)

        return result

    async def get_relationships(
        self,
        model_name: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get relationship map for a model.

        Args:
            model_name: Technical model name.
            use_cache: Use cached result if available.

        Returns:
            Dict of relationships.
        """
        cache_key = self._get_cache_key("get_relationships", model_name)
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                return cached

        # Try direct discovery if available
        if hasattr(self, 'discovery') and self.discovery:
            started = time.time()
            try:
                context = self.discovery.get_model(model_name)
                if context:
                    relationships = []
                    for f in context.fields:
                        if f.relation:
                            relationships.append({
                                "field": f.name,
                                "type": f.field_type,
                                "related_model": f.relation
                            })
                    res_data = {
                        "source": "live_odoo",
                        "model": model_name,
                        "relationships": relationships
                    }
                    self._set_cache(cache_key, res_data)
                    self._log_trace_result("get_relationships", res_data, started)
                    return res_data
            except Exception as e:
                logger.warning(f"Direct discovery get_relationships failed: {e}. Using fallback.")

        # Static fallback
        result = {
            "source": "static_fallback",
            "model": model_name,
            "relationships": [],
            "note": "MCP server not connected or failed - using static fallback"
        }

        if use_cache:
            self._set_cache(cache_key, result)

        return result

    async def validate_field(
        self,
        model_name: str,
        field_name: str,
        expected_type: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a field exists in a model.

        Args:
            model_name: Technical model name.
            field_name: Field name to validate.
            expected_type: Expected field type.
            use_cache: Use cached result if available.

        Returns:
            Validation result.
        """
        cache_key = self._get_cache_key("validate_field", model_name, field_name, expected_type)
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                return cached
        # Try direct discovery if available
        if hasattr(self, 'discovery') and self.discovery:
            started = time.time()
            try:
                context = self.discovery.get_model(model_name)
                is_valid = False
                details = {"valid": False, "note": f"Model {model_name} not found"}
                if context:
                    field = next((f for f in context.fields if f.name == field_name), None)
                    if field:
                        if expected_type and field.field_type != expected_type:
                            details = {
                                "valid": False, 
                                "note": f"Type mismatch. Expected {expected_type}, got {field.field_type}",
                                "actual_type": field.field_type
                            }
                        else:
                            is_valid = True
                            details = {"valid": True, "type": field.field_type}
                    else:
                        details = {"valid": False, "note": f"Field {field_name} not found"}
                
                res_data = {
                    "source": "live_odoo",
                    "valid": is_valid,
                    "model": model_name,
                    "field_name": field_name,
                    "details": details
                }
                self._set_cache(cache_key, res_data)
                self._log_trace_result("validate_field", res_data, started)
                return res_data
            except Exception as e:
                logger.warning(f"Direct discovery validate_field failed: {e}. Using fallback.")

        # Try live MCP call
        await self._ensure_session()
        if self._session:
            try:
                params = {"model_name": model_name, "field_name": field_name}
                if expected_type:
                    params["expected_type"] = expected_type
                    
                result = await self._call_tool_with_timeout("validate_field", params)
                parsed_result = self._parse_tool_content(result)
                if parsed_result is not None:
                    res_data = {
                        "source": "mcp_server",
                        "valid": parsed_result.get("valid"),
                        "model": model_name,
                        "field_name": field_name,
                        "details": parsed_result
                    }
                    self._set_cache(cache_key, res_data)
                    return res_data
            except Exception as e:
                logger.warning(f"MCP validate_field failed: {e}. Using static fallback.")

        # Static fallback - return unknown
        result = {
            "source": "static_fallback",
            "valid": None,
            "model": model_name,
            "field_name": field_name,
            "expected_type": expected_type,
            "note": "MCP server not connected or failed - cannot validate"
        }

        if use_cache:
            self._set_cache(cache_key, result)

        return result

    async def get_model_info(
        self,
        model_name: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get model information.

        Args:
            model_name: Technical model name.
            use_cache: Use cached result if available.

        Returns:
            Model info.
        """
        cache_key = self._get_cache_key("get_model_info", model_name)
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                return cached
        # Try direct discovery if available
        if hasattr(self, 'discovery') and self.discovery:
            started = time.time()
            try:
                context = self.discovery.get_model(model_name)
                if context:
                    res_data = {
                        "source": "live_odoo",
                        "model": model_name,
                        "info": {
                            "name": getattr(context, 'name', model_name),
                            "module": getattr(context, 'module', ''),
                            "description": getattr(context, 'description', '')
                        }
                    }
                    self._set_cache(cache_key, res_data)
                    self._log_trace_result("get_model_info", res_data, started)
                    return res_data
            except Exception as e:
                logger.warning(f"Direct discovery get_model_info failed: {e}. Using fallback.")

        # Try live MCP call
        await self._ensure_session()
        if self._session:
            try:
                result = await self._call_tool_with_timeout(
                    "get_model_info",
                    {"model_name": model_name},
                )
                parsed_result = self._parse_tool_content(result)
                if parsed_result is not None:
                    res_data = {
                        "source": "mcp_server",
                        "model": model_name,
                        "info": parsed_result
                    }
                    self._set_cache(cache_key, res_data)
                    return res_data
            except Exception as e:
                logger.warning(f"MCP get_model_info failed: {e}. Using static fallback.")

        result = {
            "source": "static_fallback",
            "model": model_name,
            "note": "MCP server not connected or failed"
        }

        if use_cache:
            self._set_cache(cache_key, result)

        return result

    async def list_all_models(
        self,
        limit: int = 100,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all available models.
        """
        cache_key = self._get_cache_key("list_all_models", limit)
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                return cached
        # Try direct discovery if available
        if hasattr(self, 'discovery') and self.discovery:
            started = time.time()
            try:
                models = self.discovery.list_models(limit=limit)
                res_data = [
                    {
                        "model": m.model,
                        "name": m.name,
                        "module": m.module,
                        "description": m.description,
                        "is_transient": m.is_transient
                    }
                    for m in models
                ]
                self._set_cache(cache_key, res_data)
                self._log_trace_result("list_all_models", res_data, started)
                return res_data
            except Exception as e:
                logger.warning(f"Direct discovery list_all_models failed: {e}. Using fallback.")

        # Try live MCP call
        await self._ensure_session()
        if self._session:
            try:
                result = await self._call_tool_with_timeout("list_all_models", {"limit": limit})
                parsed_result = self._parse_tool_content(result)
                if parsed_result is not None:
                    self._set_cache(cache_key, parsed_result)
                    return parsed_result
            except Exception as e:
                logger.warning(f"MCP list_all_models failed: {e}. Using static fallback.")

        # Static fallback
        result = [
            {"model": "res.partner", "name": "Contact", "module": "base"},
            {"model": "res.users", "name": "User", "module": "base"},
        ]

        if use_cache:
            self._set_cache(cache_key, result)

        return result

    def _get_cache_models(self, *args) -> str:
        """Generate cache key for models."""
        return self._get_cache_key("model", *args)

    # ==========================================
    # Context Loading
    # ==========================================

    async def load_context(self, version: str) -> Dict[str, Any]:
        """
        Load context for a specific Odoo version.

        Args:
            version: Odoo version (e.g., "17.0", "18.0", "19.0").

        Returns:
            Context data.
        """
        # Try to load from storage
        from .context_storage import get_storage
        storage = get_storage()

        if storage.exists(version):
            data = storage.load_context(version)
            if data:
                return {
                    "source": "storage",
                    "version": version,
                    "data": data
                }

        # Fallback to static context
        return {
            "source": "static",
            "version": version,
            "note": "No cached context available"
        }

    async def load_skill_context(self, version: str) -> Dict[str, Any]:
        """
        Load version-specific skill context.
        Priority:
        1. context.json from storage
        2. SKILL.md from OdooXXExistingDepencencyContext
        3. Static defaults
        """
        # 1. Try storage
        try:
            from .context_storage import get_storage
            storage = get_storage()
            data = storage.load_context(version)
            if data:
                return {
                    "source": "dynamic_cache",
                    "version": version,
                    "metadata": data.get("metadata", {}),
                    "model_count": data.get("metadata", {}).get("model_count", 0)
                }
        except Exception as e:
            logger.debug(f"Failed to load context from storage for {version}: {e}")

        # 2. Try SKILL.md parsing
        try:
            major_version = version.split('.')[0]
            # Use absolute path to ensure correct resolution
            base_dir = Path(__file__).resolve().parent.parent
            skill_dir = base_dir / f"Odoo{major_version}ExistingDepencencyContext"
            skill_file = skill_dir / "SKILL.md"
            
            if skill_file.exists():
                content = skill_file.read_text()
                # Simple extraction of key fields
                ref_path = ""
                for line in content.splitlines():
                    if "Standard Addons Reference Path" in line or "- Local:" in line:
                        if str(Path.home() / "workspace") in line:
                            ref_path = line.split(":")[-1].strip().strip("`")
                            break
                
                return {
                    "source": "static_skill",
                    "version": version,
                    "reference_path": ref_path,
                    "note": "Loaded from SKILL.md (Dynamic cache missing)"
                }
        except Exception as e:
            logger.debug(f"Failed to parse SKILL.md for {version}: {e}")

        # 3. Fallback
        return {
            "source": "fallback",
            "version": version,
            "note": "No context found (starting fresh)"
        }

    def refresh_context(self, version: str) -> None:
        """
        Refresh context for a version.

        Args:
            version: Odoo version.
        """
        # Clear cache for this version
        keys_to_remove = [k for k in self._cache.keys() if version in k]
        for key in keys_to_remove:
            del self._cache[key]
        logger.info(f"Refreshed context cache for {version}")


# Singleton instance
_client: Optional[OdooMcpClient] = None


def get_client(config: Optional[OdooConfig] = None) -> OdooMcpClient:
    """
    Get singleton client instance.

    Args:
        config: Optional Odoo configuration.

    Returns:
        OdooMcpClient instance.
    """
    global _client
    if _client is None:
        _client = OdooMcpClient(config)
    return _client


def reset_client() -> None:
    """Reset the singleton client instance."""
    global _client
    if _client:
        _client.clear_cache()
    _client = None

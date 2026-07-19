"""
Odoo MCP Server Module

Provides MCP server with resources, tools, and prompts for Odoo model context.
Uses FastMCP for server implementation.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
_project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(_project_dir))

import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .config import OdooConfig, load_config
from .version_detector import VersionDetector
from .protocol_handlers import create_client
from .connection_manager import ConnectionManager
from .model_extractor import ModelDiscovery, ModelContext
from .context_serializer import ContextSerializer
from .context_storage import ContextStorage

logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("odoo-mcp-server")


class OdooMcpServer:
    """Odoo MCP Server with tools and resources."""

    def __init__(self, config: Optional[OdooConfig] = None):
        """
        Initialize Odoo MCP Server.

        Args:
            config: Odoo configuration. If None, loads from environment.
        """
        self.config = config or load_config()
        self.discovery: Optional[ModelDiscovery] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.storage = ContextStorage()
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize the server (connect to Odoo).

        Returns:
            True if initialization successful.
        """
        if self._initialized:
            return True

        try:
            # Create connection manager
            self.connection_manager = ConnectionManager(self.config)
            if not self.connection_manager.initialize():
                logger.error("Failed to initialize connection manager")
                return False

            # Get client and create discovery
            client = self.connection_manager.get_connection()
            if not client:
                logger.error("Failed to get Odoo connection")
                return False

            self.discovery = ModelDiscovery(client)
            self._initialized = True

            logger.info(f"Odoo MCP Server initialized: {self.config.odoo_version} / {self.config.protocol}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            return False

    def search_models(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search models by name or description.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of model info dicts.
        """
        if not self._initialized:
            self.initialize()

        if not self.discovery:
            return [{"error": "Server not initialized"}]

        models = self.discovery.search_models(query, limit=limit)

        return [
            {
                "model": m.model,
                "name": m.name,
                "module": m.module,
                "is_transient": m.is_transient
            }
            for m in models
        ]

    def get_fields(self, model_name: str) -> Dict[str, Any]:
        """
        Get all fields for a model.

        Args:
            model_name: Technical model name.

        Returns:
            Dict of field definitions.
        """
        if not self._initialized:
            self.initialize()

        if not self.discovery:
            return {"error": "Server not initialized"}

        context = self.discovery.get_model(model_name)
        if not context:
            return {"error": f"Model not found: {model_name}"}

        return {
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
                    "help": f.help
                }
                for f in context.fields
            ]
        }

    def get_relationships(self, model_name: str) -> Dict[str, Any]:
        """
        Get relationships for a model.

        Args:
            model_name: Technical model name.

        Returns:
            Dict of relationships.
        """
        if not self._initialized:
            self.initialize()

        if not self.discovery:
            return {"error": "Server not initialized"}

        context = self.discovery.get_model(model_name)
        if not context:
            return {"error": f"Model not found: {model_name}"}

        return {
            "model": context.model.model,
            "relationships": [
                {
                    "name": r.name,
                    "type": r.type,
                    "relation": r.relation,
                    "inverse_name": r.inverse_name
                }
                for r in context.relationships
            ]
        }

    def validate_field(
        self,
        model_name: str,
        field_name: str,
        expected_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a field exists in a model.

        Args:
            model_name: Technical model name.
            field_name: Field name to validate.
            expected_type: Expected field type.

        Returns:
            Validation result.
        """
        if not self._initialized:
            self.initialize()

        if not self.discovery:
            return {"error": "Server not initialized"}

        context = self.discovery.get_model(model_name)
        if not context:
            return {"error": f"Model not found: {model_name}"}

        # Find field
        field = None
        for f in context.fields:
            if f.name == field_name:
                field = f
                break

        if not field:
            return {
                "valid": False,
                "reason": f"Field '{field_name}' not found in model '{model_name}'",
                "available_fields": [f.name for f in context.fields[:10]]
            }

        # Check type if specified
        if expected_type and field.field_type != expected_type:
            return {
                "valid": False,
                "reason": f"Field '{field_name}' has type '{field.field_type}', expected '{expected_type}'",
                "field_type": field.field_type
            }

        return {
            "valid": True,
            "field_name": field.name,
            "field_type": field.field_type,
            "string": field.string,
            "required": field.required,
            "readonly": field.readonly,
            "relation": field.relation
        }

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get model information.

        Args:
            model_name: Technical model name.

        Returns:
            Model info dict.
        """
        if not self._initialized:
            self.initialize()

        if not self.discovery:
            return {"error": "Server not initialized"}

        context = self.discovery.get_model(model_name)
        if not context:
            return {"error": f"Model not found: {model_name}"}

        return {
            "model": context.model.model,
            "name": context.model.name,
            "description": context.model.description,
            "is_transient": context.model.is_transient,
            "module": context.model.module,
            "field_count": len(context.fields),
            "relationship_count": len(context.relationships)
        }

    def list_all_models(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all available models.

        Args:
            limit: Maximum results.

        Returns:
            List of model info dicts.
        """
        if not self._initialized:
            self.initialize()

        if not self.discovery:
            return [{"error": "Server not initialized"}]

        models = self.discovery.list_models(limit=limit)

        return [
            {
                "model": m.model,
                "name": m.name,
                "module": m.module,
                "is_transient": m.is_transient
            }
            for m in models
        ]

    def close(self) -> None:
        """Close the server and cleanup connections."""
        if self.connection_manager:
            self.connection_manager.close_all()
        self._initialized = False
        logger.info("Odoo MCP Server closed")


# Global server instance
_server: Optional[OdooMcpServer] = None


def get_server() -> OdooMcpServer:
    """Get singleton server instance."""
    global _server
    if _server is None:
        _server = OdooMcpServer()
    return _server


# ============================================
# MCP Server Tools (FastMCP decorators)
# ============================================


@mcp.tool()
async def search_models(query: str, limit: int = 20) -> str:
    """
    Search Odoo models by name or description.

    Args:
        query: Search query string.
        limit: Maximum number of results (default: 20).

    Returns:
        JSON string of matching models.
    """
    import time
    started = time.time()
    logger.info("MCP TOOL search_models start query=%s limit=%s", query, limit)
    server = get_server()
    results = server.search_models(query, limit=limit)
    logger.info("MCP TOOL search_models done count=%s took=%sms", len(results or []), int((time.time() - started) * 1000))
    import json
    return json.dumps(results, indent=2)


@mcp.tool()
async def get_fields(model_name: str) -> str:
    """
    Get all fields for an Odoo model.

    Args:
        model_name: Technical model name (e.g., 'res.partner').

    Returns:
        JSON string of field definitions.
    """
    import time
    started = time.time()
    logger.info("MCP TOOL get_fields start model=%s", model_name)
    server = get_server()
    results = server.get_fields(model_name)
    fields_count = len((results or {}).get("fields", [])) if isinstance(results, dict) else 0
    logger.info("MCP TOOL get_fields done model=%s fields=%s took=%sms", model_name, fields_count, int((time.time() - started) * 1000))
    import json
    return json.dumps(results, indent=2)


@mcp.tool()
async def get_relationships(model_name: str) -> str:
    """
    Get relationship map for an Odoo model.

    Args:
        model_name: Technical model name (e.g., 'res.partner').

    Returns:
        JSON string of relationships.
    """
    import time
    started = time.time()
    logger.info("MCP TOOL get_relationships start model=%s", model_name)
    server = get_server()
    results = server.get_relationships(model_name)
    rel_count = len((results or {}).get("relationships", [])) if isinstance(results, dict) else 0
    logger.info("MCP TOOL get_relationships done model=%s relationships=%s took=%sms", model_name, rel_count, int((time.time() - started) * 1000))
    import json
    return json.dumps(results, indent=2)


@mcp.tool()
async def validate_field(
    model_name: str,
    field_name: str,
    expected_type: Optional[str] = None
) -> str:
    """
    Validate a field exists in a model.

    Args:
        model_name: Technical model name (e.g., 'res.partner').
        field_name: Field name to validate.
        expected_type: Optional expected field type (e.g., 'many2one').

    Returns:
        JSON string of validation result.
    """
    import time
    started = time.time()
    logger.info("MCP TOOL validate_field start model=%s field=%s expected=%s", model_name, field_name, expected_type)
    server = get_server()
    results = server.validate_field(model_name, field_name, expected_type)
    logger.info("MCP TOOL validate_field done model=%s field=%s valid=%s took=%sms", model_name, field_name, (results or {}).get("valid"), int((time.time() - started) * 1000))
    import json
    return json.dumps(results, indent=2)


@mcp.tool()
async def get_model_info(model_name: str) -> str:
    """
    Get information about an Odoo model.

    Args:
        model_name: Technical model name (e.g., 'res.partner').

    Returns:
        JSON string of model information.
    """
    server = get_server()
    results = server.get_model_info(model_name)
    import json
    return json.dumps(results, indent=2)


@mcp.tool()
async def get_version_info() -> str:
    """
    Get the current Odoo version and connection info for this MCP server instance.

    Returns:
        JSON string with version, protocol, host, port, and database info.
    """
    server = get_server()
    if not server._initialized:
        server.initialize()
    cfg = server.config
    import json
    return json.dumps({
        "odoo_version": cfg.odoo_version,
        "protocol": cfg.protocol,
        "host": cfg.host,
        "port": cfg.port,
        "database": cfg.database,
        "username": cfg.username,
        "mcp_server_port": cfg.mcp_server_port,
        "status": "connected" if server._initialized else "disconnected"
    }, indent=2)


@mcp.tool()
async def list_all_models(limit: int = 100) -> str:
    """
    List all available Odoo models.

    Args:
        limit: Maximum number of results (default: 100).

    Returns:
        JSON string of model list.
    """
    server = get_server()
    results = server.list_all_models(limit=limit)
    import json
    return json.dumps(results, indent=2)


# ============================================
# MCP Server Resources
# ============================================


@mcp.resource("models://list")
async def list_models_resource() -> str:
    """List all available models as a resource."""
    server = get_server()
    results = server.list_all_models(limit=500)
    import json
    return json.dumps(results, indent=2)


@mcp.resource("models://{model_name}")
async def get_model_resource(model_name: str) -> str:
    """Get detailed model information as a resource."""
    server = get_server()
    results = server.get_model_info(model_name)
    import json
    return json.dumps(results, indent=2)


# ============================================
# MCP Server Prompts
# ============================================


@mcp.prompt()
def generate_model_code_prompt(model_name: str, version: str = "19.0") -> str:
    """
    Generate a prompt for creating Odoo model code.

    Args:
        model_name: Name of the model to generate code for.
        version: Odoo version (default: 19.0).

    Returns:
        Prompt string.
    """
    return f"""Generate an Odoo {version} model code scaffold for model '{model_name}'.

Use the following structure:
```python
from odoo import models, fields

class {model_name.replace('.', '_')}(models.Model):
    _name = '{model_name}'
    _description = 'Model description'

    name = fields.Char(string='Name', required=True)
    # Add more fields based on the model's fields from the database
```

Make sure to include appropriate field types based on the database schema."""


@mcp.prompt()
def analyze_model_prompt(model_name: str) -> str:
    """
    Generate a prompt for analyzing an Odoo model.

    Args:
        model_name: Name of the model to analyze.

    Returns:
        Prompt string.
    """
    return f"""Analyze the Odoo model '{model_name}' and provide:
1. Overview of the model's purpose
2. Key fields and their types
3. Relationships with other models
4. Potential customizations or extensions needed
5. Security considerations

Use the MCP tools to fetch the model's fields and relationships."""


# ============================================
# Server startup
# ============================================


def run_server(
    host: str = "localhost",
    port: int = 8765,
    config: Optional[OdooConfig] = None,
    transport: str = "stdio",
    version: Optional[str] = None
) -> None:
    """
    Run the MCP server.

    Args:
        host: Server host.
        port: Server port.
        config: Optional Odoo configuration.
        transport: Transport mode (stdio or sse).
    """
    global _server
    if config:
        _server = OdooMcpServer(config)
    elif version:
        from .config import load_config as _load_config
        _server = OdooMcpServer(_load_config(version))

    effective_version = (_server.config.odoo_version if _server else version) or "auto"
    logger.info(f"Starting Odoo MCP Server on {host}:{port} (transport: {transport}, version: {effective_version})")

    if transport == "sse":
        # Run HTTP server using FastMCP's built-in SSE transport
        app = mcp.sse_app()

        import uvicorn
        logger.info(f"Starting SSE server on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
    else:
        # Standard stdio mode for Claude Code integration
        mcp.run(transport="stdio")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Odoo MCP Server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    parser.add_argument("--version", help="Odoo version (17.0, 18.0, 19.0)")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="Transport mode")

    args = parser.parse_args()

    # Load config - version from CLI arg OR DEFAULT_ODOO_VERSION env var
    import os
    effective_version = args.version or os.environ.get("DEFAULT_ODOO_VERSION", "19.0")
    config = load_config(effective_version)

    run_server(
        host=args.host,
        port=args.port,
        config=config,
        transport=args.transport,
        version=effective_version
    )

#!/usr/bin/env python3
"""
Entry point for running the MCP server.

Usage:
    python -m mcp.server
    python -m mcp.server --port 8090
    python -m mcp.server --version 17.0
"""

import sys
import argparse
from pathlib import Path

# Ensure the parent directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp import OdooMcpServer


def main():
    parser = argparse.ArgumentParser(description="Odoo MCP Server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8090, help="Server port")
    parser.add_argument("--version", help="Specific Odoo version (17.0, 18.0, 19.0)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Import and run the server
    from odoo_mcp.server.fastmcp import FastMCP
    from odoo_mcp.types import TextContent
    from odoo_mcp.config import OdooConfig, load_config
    from odoo_mcp.version_detector import VersionDetector
    from odoo_mcp.protocol_handlers import create_client
    from odoo_mcp.connection_manager import ConnectionManager
    from odoo_mcp.model_extractor import ModelDiscovery, ModelContext
    from odoo_mcp.context_serializer import ContextSerializer
    from odoo_mcp.context_storage import ContextStorage
    import logging

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)

    # Create MCP server
    mcp = FastMCP("odoo-mcp-server")

    # Server implementation would go here
    # For now, just print info
    logger.info(f"Starting Odoo MCP Server on {args.host}:{args.port}")
    if args.version:
        logger.info(f"Targeting Odoo version: {args.version}")

    # Run the server in stdio mode (for Claude Code)
    print("Odoo MCP Server ready", file=sys.stderr)
    print("Server running in stdio mode", file=sys.stderr)


if __name__ == "__main__":
    main()

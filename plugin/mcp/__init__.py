"""
Odoo MCP Server Package

This package provides a Model Context Protocol (MCP) server for connecting to
Odoo 17, 18, and 19 instances via XML-RPC (17-18) and JSON-RPC 2.0 (19).

Package Structure:
- config.py: OdooConfig Pydantic model + .env parser
- version_detector.py: Auto-detect Odoo version + protocol selector
- protocol_handlers.py: BaseClient, XmlRpcClient, JsonRpc20Client
- connection_manager.py: Connection pool + retry logic
- model_extractor.py: ir.model + ir.model.fields queries
- context_serializer.py: JSON output + index generation
- context_storage.py: Atomic writes to version-specific dirs
- odoo_mcp_server.py: MCP server: resources, tools, prompts
- client.py: OdooMcpClient wrapper
- utils.py: Shared utilities

Protocol Support:
- Odoo 17: XML-RPC (/xmlrpc/2/object)
- Odoo 18: XML-RPC (/xmlrpc/2/object)
- Odoo 19: JSON-RPC 2.0 (/jsonrpc)

Version: 1.0.0
"""

__version__ = "1.0.0"

def __getattr__(name):
    """Lazy imports for the package."""
    if name == "OdooConfig":
        from .config import OdooConfig
        return OdooConfig
    elif name == "load_config":
        from .config import load_config
        return load_config
    elif name == "VersionDetector":
        from .version_detector import VersionDetector
        return VersionDetector
    elif name == "BaseClient":
        from .protocol_handlers import BaseClient
        return BaseClient
    elif name == "XmlRpcClient":
        from .protocol_handlers import XmlRpcClient
        return XmlRpcClient
    elif name == "JsonRpc20Client":
        from .protocol_handlers import JsonRpc20Client
        return JsonRpc20Client
    elif name == "ConnectionManager":
        from .connection_manager import ConnectionManager
        return ConnectionManager
    elif name == "ConnectionPool":
        from .connection_manager import ConnectionPool
        return ConnectionPool
    elif name == "ModelExtractor":
        from .model_extractor import ModelExtractor
        return ModelExtractor
    elif name == "ModelDiscovery":
        from .model_extractor import ModelDiscovery
        return ModelDiscovery
    elif name == "ContextSerializer":
        from .context_serializer import ContextSerializer
        return ContextSerializer
    elif name == "ContextStorage":
        from .context_storage import ContextStorage
        return ContextStorage
    elif name == "OdooMcpClient":
        from .client import OdooMcpClient
        return OdooMcpClient
    elif name == "setup_logging":
        from .utils import setup_logging
        return setup_logging
    elif name == "handle_errors":
        from .utils import handle_errors
        return handle_errors
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

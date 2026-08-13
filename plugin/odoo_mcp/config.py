"""
Odoo MCP Configuration Module

Provides OdooConfig Pydantic model and .env parser for MCP server settings.
Reuses existing .env variables: ODOO_DB_NAME, ODOO_URL, ODOO_DB_USER, ODOO_DB_PASSWORD.
"""

import os
import logging
from typing import Optional, Literal
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from dotenv import dotenv_values, load_dotenv

# Load .env file
# override=False so that env vars already set in the process environment
# (e.g. version-specific ODOO_URL passed by start_mcp_server.sh) take priority
# over the generic values in .env.
load_dotenv(override=False)

logger = logging.getLogger(__name__)


def load_session_environment() -> None:
    """Resolve session-scoped Compose settings without overriding explicit env."""
    manifest_path = Path(os.environ.get("SANDBOX_SESSION_FILE", ".sandbox/session.json"))
    if not manifest_path.is_file():
        return
    try:
        manifest = __import__("json").loads(manifest_path.read_text())
        session_id = manifest["session_id"]
        runtime_env = manifest_path.parent / "sessions" / session_id / "runtime.env"
        values = dotenv_values(runtime_env) if runtime_env.is_file() else {}
        os.environ.setdefault("DEFAULT_ODOO_VERSION", manifest["odoo_version"])
        os.environ.setdefault("ODOO_URL", "http://odoo:8069")
        os.environ.setdefault("ODOO_DB_NAME", str(values.get("ODOO_DB_NAME", "sandbox_db")))
        os.environ.setdefault("ODOO_DB_USER", "admin")
        os.environ.setdefault("ODOO_DB_PASSWORD", str(values.get("ODOO_API_PASSWORD", "")))
        os.environ.setdefault("MCP_SERVER_HOST", "0.0.0.0")
    except (KeyError, OSError, ValueError) as exc:
        logger.warning("Unable to load sandbox session manifest %s: %s", manifest_path, exc)


class OdooConfig(BaseModel):
    """Odoo connection configuration for MCP server."""

    # Connection settings
    host: str = Field(default="localhost", description="Odoo server host")
    port: int = Field(default=8069, ge=1, le=65535, description="Odoo server port")
    database: str = Field(..., description="Odoo database name")
    username: str = Field(default="admin", description="Odoo username")
    password: str = Field(..., description="Odoo password")

    # Version settings
    odoo_version: Optional[str] = Field(default=None, description="Odoo version (auto-detect if not set)")

    # MCP server settings
    mcp_server_host: str = Field(default="localhost", description="MCP server host")
    mcp_server_port: int = Field(default=8765, ge=1, le=65535, description="MCP server port")

    # Cache and performance settings
    cache_ttl: int = Field(default=3600, ge=60, description="Cache TTL in seconds")
    connection_pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    request_timeout: int = Field(default=30, ge=5, le=300, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, ge=1, le=10, description="Retry attempts for failed requests")

    # Feature flags
    lazy_loading: bool = Field(default=True, description="Load models on demand")
    auto_refresh: bool = Field(default=True, description="Auto-refresh context on version switch")

    # Protocol (auto-selected based on version)
    protocol: Optional[Literal["xml-rpc", "json-rpc-2.0"]] = Field(default=None, description="Protocol to use")

    @field_validator("odoo_version")
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate Odoo version format."""
        if v is None:
            return None
        # Accept formats like "17.0", "18", "19.0"
        if not v.replace(".", "").isdigit():
            raise ValueError(f"Invalid version format: {v}")
        return v

    def get_base_url(self) -> str:
        """Get the base URL for Odoo server."""
        return f"http://{self.host}:{self.port}"

    def get_rpc_endpoint(self) -> str:
        """Get the RPC endpoint based on protocol."""
        if self.protocol == "json-rpc-2.0":
            return f"{self.get_base_url()}/jsonrpc"
        return f"{self.get_base_url()}/xmlrpc/2/object"

    class Config:
        extra = "allow"


def load_config(version: Optional[str] = None) -> OdooConfig:
    """
    Load Odoo configuration from environment variables.

    Args:
        version: Optional version override (e.g., "17.0", "18.0", "19.0").
                 If not provided, uses DEFAULT_ODOO_VERSION or "19.0".

    Returns:
        OdooConfig instance with loaded settings.

    Environment Variables (per version):
        - ODOO_URL: Base URL (e.g., http://localhost:8069)
        - ODOO_DB_NAME: Database name
        - ODOO_DB_USER: Username (default: admin)
        - ODOO_DB_PASSWORD: Password

    Version-specific overrides:
        - ODOO17_URL, ODOO17_DB_NAME, ODOO17_DB_USER, ODOO17_DB_PASSWORD
        - ODOO18_URL, ODOO18_DB_NAME, ODOO18_DB_USER, ODOO18_DB_PASSWORD
        - ODOO19_URL, ODOO19_DB_NAME, ODOO19_DB_USER, ODOO19_DB_PASSWORD
    """
    load_session_environment()
    # Determine version
    if version is None:
        version = os.environ.get("DEFAULT_ODOO_VERSION", "19.0")

    # Normalize version (e.g., "19" -> "19.0")
    if version and "." not in version:
        version = f"{version}.0"

    # Build prefix for version-specific env vars
    # CRITICAL: Use MAJOR version only: "17.0"->"17", "18.0"->"18", "19.0"->"19"
    # (NOT version.replace(".","") which gives "170","180" - those vars don't exist)
    version_prefix = version.split(".")[0]  # "17.0" -> "17"

    # Helper to get env var with version fallback
    def get_odoo_env(key: str, default: str = "") -> str:
        """Get Odoo env var with version-specific fallback.
        Priority: ODOO17_URL > ODOO_URL (generic/v19)
        .env has: ODOO17_URL, ODOO18_URL, ODOO_URL (for 19)
        """
        versioned = os.environ.get(f"ODOO{version_prefix}_{key}")
        if versioned:
            return versioned
        # Fallback to generic (canonical for v19, last resort for others)
        generic = os.environ.get(f"ODOO_{key}")
        if generic:
            return generic
        return default

    # Extract host and port from URL
    url = get_odoo_env("URL", "http://localhost:8069")
    # Parse host:port from URL
    host = "localhost"
    port = 8069
    if "://" in url:
        url_without_scheme = url.split("://", 1)[1]
        if ":" in url_without_scheme:
            host, port_str = url_without_scheme.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                pass
        else:
            host = url_without_scheme

    # Get database and credentials
    # NOTE: DB_USER / DB_PASSWORD are Odoo APPLICATION login credentials
    # (the username + password you type on the Odoo web login page), NOT the
    # PostgreSQL database system user.  Common values: username='admin', password='admin'.
    database = get_odoo_env("DB_NAME", "")
    username = get_odoo_env("DB_USER", "admin")   # Odoo login user (not postgres user)
    password = get_odoo_env("DB_PASSWORD", "")    # Odoo login password (not postgres password)

    if not database:
        logger.warning("ODOO_DB_NAME not set, using empty database name")
    if not password:
        logger.warning("ODOO_DB_PASSWORD not set, using empty password")

    # Determine protocol based on version
    protocol: Optional[Literal["xml-rpc", "json-rpc-2.0"]] = None
    major_version = int(version.split(".")[0]) if version else 19

    if major_version >= 19:
        protocol = "json-rpc-2.0"
    else:
        protocol = "xml-rpc"

    # Get MCP settings
    mcp_server_host = os.environ.get("MCP_SERVER_HOST", "localhost")
    
    # Version-aware port detection (Phase 12)
    default_mcp_ports = {"17.0": 8765, "18.0": 8766, "19.0": 8767}
    
    # Priority: 1. Specific env, 2. Version default, 3. Generic env
    # version_prefix is already the major number (17, 18, 19)
    mcp_server_port_str = os.environ.get(f"MCP{version_prefix}_SERVER_PORT")
    if mcp_server_port_str:
        mcp_server_port = int(mcp_server_port_str)
    elif version in default_mcp_ports:
        mcp_server_port = default_mcp_ports[version]
    else:
        mcp_server_port = int(os.environ.get("MCP_SERVER_PORT", "8765"))
    
    # Load other MCP settings
    cache_ttl = int(os.environ.get("MCP_CONTEXT_CACHE_TTL", "3600"))
    connection_pool_size = int(os.environ.get("MCP_CONNECTION_POOL_SIZE", "10"))
    request_timeout = int(os.environ.get("MCP_REQUEST_TIMEOUT", "30"))
    retry_attempts = int(os.environ.get("MCP_RETRY_ATTEMPTS", "3"))
    lazy_loading = os.environ.get("MCP_LAZY_LOADING", "true").lower() == "true"
    auto_refresh = os.environ.get("MCP_AUTO_REFRESH", "true").lower() == "true"

    config = OdooConfig(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        odoo_version=version,
        mcp_server_host=mcp_server_host,
        mcp_server_port=mcp_server_port,
        cache_ttl=cache_ttl,
        connection_pool_size=connection_pool_size,
        request_timeout=request_timeout,
        retry_attempts=retry_attempts,
        lazy_loading=lazy_loading,
        auto_refresh=auto_refresh,
        protocol=protocol,
    )

    logger.info(
        f"Loaded Odoo config: version={version}, protocol={config.protocol}, "
        f"host={config.host}:{config.port}, db={config.database}"
    )

    return config


# Convenience function for quick config loading
def get_default_config() -> OdooConfig:
    """Get default configuration for the current Odoo version."""
    return load_config()

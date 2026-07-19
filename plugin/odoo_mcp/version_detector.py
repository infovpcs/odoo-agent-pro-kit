"""
Odoo Version Detection Module

Auto-detects Odoo version and selects appropriate protocol:
- Odoo 17 -> XML-RPC (/xmlrpc/2/object)
- Odoo 18 -> XML-RPC (/xmlrpc/2/object)
- Odoo 19 -> JSON-RPC 2.0 (/jsonrpc)
"""

import logging
import xmlrpc.client
from typing import Optional, Tuple, Literal

import requests

from .config import OdooConfig

logger = logging.getLogger(__name__)

Protocol = Literal["xml-rpc", "json-rpc-2.0"]


class VersionDetector:
    """Detects Odoo version and selects appropriate RPC protocol."""

    # Version to protocol mapping
    VERSION_PROTOCOL_MAP = {
        17: "xml-rpc",
        18: "xml-rpc",
        19: "json-rpc-2.0",
    }

    def __init__(self, config: OdooConfig):
        """Initialize version detector with Odoo configuration."""
        self.config = config

    def detect_version(self) -> Optional[str]:
        """
        Detect Odoo version from the database.

        Returns:
            Version string (e.g., "17.0", "18.0", "19.0") or None if detection fails.
        """
        # Try to get version from config first
        if self.config.odoo_version:
            return self.config.odoo_version

        # Try to detect from database
        version = self._detect_from_database()
        if version:
            logger.info(f"Detected Odoo version: {version}")
            return version

        # Fallback based on protocol
        if self.config.protocol:
            return self._version_from_protocol(self.config.protocol)

        # Default to 19.0
        logger.warning("Could not detect Odoo version, defaulting to 19.0")
        return "19.0"

    def _detect_from_database(self) -> Optional[str]:
        """Query database to detect Odoo version."""
        try:
            # Try XML-RPC first (works for 17, 18, and 19)
            common = xmlrpc.client.ServerProxy(f"{self.config.get_base_url()}/xmlrpc/2/common")
            version_info = common.version()

            if isinstance(version_info, dict):
                version_string = version_info.get("version", "")
                # Parse version like "17.0" or "SaaS~19.0"
                if "~" in version_string:
                    # SaaS version format: "SaaS~19.0"
                    version = version_string.split("~")[-1]
                else:
                    version = version_string

                # Normalize to X.0 format
                if "." not in version:
                    version = f"{version}.0"

                logger.info(f"Detected version from database: {version}")
                return version

        except Exception as e:
            logger.debug(f"XML-RPC version detection failed: {e}")

        # Try JSON-RPC for Odoo 19
        try:
            if self.config.protocol == "json-rpc-2.0":
                response = requests.post(
                    f"{self.config.get_base_url()}/jsonrpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "call",
                        "params": {"service": "common", "method": "version", "args": []},
                        "id": 1,
                    },
                    timeout=5,
                )
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result:
                        version_string = str(result["result"])
                        if "19" in version_string:
                            return "19.0"
        except Exception as e:
            logger.debug(f"JSON-RPC version detection failed: {e}")

        return None

    def _version_from_protocol(self, protocol: Protocol) -> str:
        """Get default version from protocol."""
        if protocol == "json-rpc-2.0":
            return "19.0"
        # Default to 17 for XML-RPC
        return "17.0"

    def get_protocol(self, version: Optional[str] = None) -> Protocol:
        """
        Get the appropriate RPC protocol for the given Odoo version.

        Args:
            version: Odoo version string (e.g., "17.0", "18.0", "19.0").
                    If None, uses auto-detection.

        Returns:
            Protocol string: "xml-rpc" or "json-rpc-2.0"
        """
        if version is None:
            version = self.detect_version()

        if version is None:
            # Default to XML-RPC
            logger.warning("Could not determine version, defaulting to XML-RPC")
            return "xml-rpc"

        # Extract major version
        try:
            major = int(version.split(".")[0])
        except (ValueError, IndexError):
            major = 17

        # Get protocol from mapping
        protocol = self.VERSION_PROTOCOL_MAP.get(major, "xml-rpc")

        logger.info(f"Selected protocol {protocol} for Odoo {version}")
        return protocol

    def get_endpoint(self, version: Optional[str] = None) -> str:
        """
        Get the RPC endpoint URL for the given Odoo version.

        Args:
            version: Odoo version string. If None, uses auto-detection.

        Returns:
            Full RPC endpoint URL.
        """
        protocol = self.get_protocol(version)

        if protocol == "json-rpc-2.0":
            return f"{self.config.get_base_url()}/jsonrpc"
        return f"{self.config.get_base_url()}/xmlrpc/2/object"

    @classmethod
    def validate_connection(cls, config: OdooConfig) -> Tuple[bool, str]:
        """
        Validate Odoo connection and return status.

        Args:
            config: Odoo configuration.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Try XML-RPC common endpoint
            common = xmlrpc.client.ServerProxy(f"{config.get_base_url()}/xmlrpc/2/common")
            uid = common.authenticate(
                config.database,
                config.username,
                config.password,
                {}
            )

            if uid:
                return True, f"Connected successfully (UID: {uid})"
            else:
                return False, "Authentication failed - invalid credentials"

        except xmlrpc.client.Error as e:
            return False, f"XML-RPC error: {str(e)}"
        except requests.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"


def detect_odoo_version(config: OdooConfig) -> str:
    """
    Convenience function to detect Odoo version.

    Args:
        config: Odoo configuration.

    Returns:
        Detected version string (e.g., "17.0", "18.0", "19.0").
    """
    detector = VersionDetector(config)
    return detector.detect_version()


def get_protocol_for_version(version: str) -> Protocol:
    """
    Convenience function to get protocol for version.

    Args:
        version: Odoo version string.

    Returns:
        Protocol: "xml-rpc" or "json-rpc-2.0"
    """
    detector = VersionDetector(OdooConfig(database="dummy", password="dummy"))
    return detector.get_protocol(version)

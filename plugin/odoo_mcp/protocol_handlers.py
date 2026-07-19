"""
Odoo Protocol Handlers Module

Provides protocol abstraction layer for Odoo RPC communication:
- BaseClient: Abstract base class for RPC clients
- XmlRpcClient: XML-RPC client for Odoo 17-18
- JsonRpc20Client: JSON-RPC 2.0 client for Odoo 19

Based on patterns from Gradio-Mcp-Odoo reference implementation.
"""

import logging
import xmlrpc.client
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import requests

from .config import OdooConfig

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """Abstract base class for Odoo RPC clients."""

    def __init__(self, config: OdooConfig):
        """Initialize base client with configuration."""
        self.config = config
        self.uid: Optional[int] = None
        self._authenticated = False

    @abstractmethod
    def authenticate(self) -> Optional[int]:
        """
        Authenticate with Odoo server.

        Returns:
            User ID (uid) on success, None on failure.
        """
        pass

    @abstractmethod
    def execute_kw(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Execute a method on an Odoo model.

        Args:
            model: Odoo model name (e.g., 'res.partner')
            method: Method name (e.g., 'search_read', 'create')
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result or error.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the connection."""
        pass

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._authenticated and self.uid is not None


class XmlRpcClient(BaseClient):
    """XML-RPC client for Odoo 17 and 18."""

    def __init__(self, config: OdooConfig):
        """Initialize XML-RPC client."""
        super().__init__(config)
        self.common_proxy: Optional[xmlrpc.client.ServerProxy] = None
        self.models_proxy: Optional[xmlrpc.client.ServerProxy] = None

    def authenticate(self) -> Optional[int]:
        """
        Authenticate with Odoo using XML-RPC.

        Returns:
            User ID (uid) on success, None on failure.
        """
        try:
            # Create common endpoint proxy
            self.common_proxy = xmlrpc.client.ServerProxy(
                f"{self.config.get_base_url()}/xmlrpc/2/common",
                allow_none=True
            )

            # Authenticate
            self.uid = self.common_proxy.authenticate(
                self.config.database,
                self.config.username,
                self.config.password,
                {}
            )

            if self.uid:
                self._authenticated = True
                logger.info(f"XML-RPC authenticated successfully (UID: {self.uid})")

                # Create models proxy for execute_kw
                self.models_proxy = xmlrpc.client.ServerProxy(
                    f"{self.config.get_base_url()}/xmlrpc/2/object",
                    allow_none=True
                )
                return self.uid
            else:
                logger.warning("XML-RPC authentication failed - invalid credentials")
                return None

        except xmlrpc.client.Error as e:
            logger.error(f"XML-RPC authentication error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected XML-RPC authentication error: {e}")
            return None

    def execute_kw(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Execute a method on an Odoo model via XML-RPC.

        Args:
            model: Odoo model name
            method: Method name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result or error dict.
        """
        if not self._authenticated:
            if not self.authenticate():
                return {"error": "Authentication failed"}

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        try:
            # Remove 'raise_exception' for methods that don't support it
            methods_without_raise_exception = ["create", "write", "unlink"]
            if method in methods_without_raise_exception:
                kwargs.pop("raise_exception", None)

            result = self.models_proxy.execute_kw(
                self.config.database,
                self.uid,
                self.config.password,
                model,
                method,
                args,
                kwargs
            )
            return result

        except xmlrpc.client.Fault as e:
            error_msg = f"XML-RPC fault: {e.faultString}"
            logger.error(error_msg)
            return {"error": error_msg}
        except xmlrpc.client.Error as e:
            error_msg = f"XML-RPC error: {e}"
            logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            return {"error": error_msg}

    def close(self) -> None:
        """Close XML-RPC connection."""
        self._authenticated = False
        self.uid = None
        self.common_proxy = None
        self.models_proxy = None
        logger.info("XML-RPC connection closed")

    # Convenience methods
    def search(
        self,
        model: str,
        domain: Optional[List] = None,
        limit: int = 0
    ) -> Union[List[int], Dict]:
        """
        Search for records.

        Args:
            model: Odoo model name
            domain: Search domain
            limit: Maximum number of records

        Returns:
            List of record IDs or error dict.
        """
        if domain is None:
            domain = []
        return self.execute_kw(model, "search", [domain], {"limit": limit})

    def search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        limit: int = 100
    ) -> Union[List[Dict], Dict]:
        """
        Search and read records.

        Args:
            model: Odoo model name
            domain: Search domain
            fields: Fields to read
            limit: Maximum number of records

        Returns:
            List of records or error dict.
        """
        if domain is None:
            domain = []
        kwargs = {"limit": limit}
        if fields:
            kwargs["fields"] = fields
        return self.execute_kw(model, "search_read", [domain], kwargs)

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None
    ) -> Union[List[Dict], Dict]:
        """
        Read records by IDs.

        Args:
            model: Odoo model name
            ids: List of record IDs
            fields: Fields to read

        Returns:
            List of records or error dict.
        """
        kwargs = {}
        if fields:
            kwargs["fields"] = fields
        return self.execute_kw(model, "read", [ids], kwargs)

    def create(
        self,
        model: str,
        values: Dict
    ) -> Union[int, Dict]:
        """
        Create a new record.

        Args:
            model: Odoo model name
            values: Field values

        Returns:
            Created record ID or error dict.
        """
        return self.execute_kw(model, "create", [values], {})

    def write(
        self,
        model: str,
        ids: List[int],
        values: Dict
    ) -> Union[bool, Dict]:
        """
        Update records.

        Args:
            model: Odoo model name
            ids: List of record IDs
            values: Field values to update

        Returns:
            True or error dict.
        """
        return self.execute_kw(model, "write", [ids, values], {})

    def unlink(
        self,
        model: str,
        ids: List[int]
    ) -> Union[bool, Dict]:
        """
        Delete records.

        Args:
            model: Odoo model name
            ids: List of record IDs

        Returns:
            True or error dict.
        """
        return self.execute_kw(model, "unlink", [ids], {})

    def fields_get(
        self,
        model: str,
        attributes: Optional[List[str]] = None
    ) -> Union[Dict, Dict]:
        """
        Get field definitions for a model.

        Args:
            model: Odoo model name
            attributes: List of attributes to return

        Returns:
            Dict of field definitions or error dict.
        """
        if attributes is None:
            attributes = ["string", "type", "help", "readonly", "required", "relation", "selection"]
        return self.execute_kw(model, "fields_get", [], {"attributes": attributes})


class JsonRpc20Client(BaseClient):
    """JSON-RPC 2.0 client for Odoo 19."""

    def __init__(self, config: OdooConfig):
        """Initialize JSON-RPC 2.0 client."""
        super().__init__(config)
        self.session = requests.Session()
        self.request_id = 0

    def _generate_id(self) -> int:
        """Generate unique request ID."""
        self.request_id += 1
        return self.request_id

    def _make_request(
        self,
        method: str,
        service: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Dict:
        """
        Make a JSON-RPC 2.0 request.

        Args:
            method: RPC method name
            service: Service name (common, object, db)
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Response dict.
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args + [kwargs] if kwargs else args
            },
            "id": self._generate_id()
        }

        try:
            response = self.session.post(
                f"{self.config.get_base_url()}/jsonrpc",
                json=payload,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                return {"error": result["error"]}

            return result.get("result", {})

        except requests.RequestException as e:
            logger.error(f"JSON-RPC request error: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected JSON-RPC error: {e}")
            return {"error": str(e)}

    def authenticate(self) -> Optional[int]:
        """
        Authenticate with Odoo using JSON-RPC 2.0.

        Returns:
            User ID (uid) on success, None on failure.
        """
        result = self._make_request(
            "authenticate",
            "common",
            args=[
                self.config.database,
                self.config.username,
                self.config.password,
                {}
            ]
        )

        if isinstance(result, dict) and "error" in result:
            logger.error(f"JSON-RPC authentication error: {result['error']}")
            return None

        if result:
            self.uid = int(result)
            self._authenticated = True
            logger.info(f"JSON-RPC authenticated successfully (UID: {self.uid})")
            return self.uid

        logger.warning("JSON-RPC authentication failed - invalid credentials")
        return None

    def execute_kw(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Execute a method on an Odoo model via JSON-RPC 2.0.

        Args:
            model: Odoo model name
            method: Method name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result or error dict.
        """
        if not self._authenticated:
            if not self.authenticate():
                return {"error": "Authentication failed"}

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        # Build args for JSON-RPC
        full_args = [self.config.database, self.uid, self.config.password, model, method, args, kwargs]

        result = self._make_request("execute_kw", "object", args=full_args)

        if isinstance(result, dict) and "error" in result:
            error_msg = result.get("error", {})
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))
            logger.error(f"JSON-RPC execute_kw error: {error_msg}")
            return {"error": error_msg}

        return result

    def close(self) -> None:
        """Close JSON-RPC connection."""
        self._authenticated = False
        self.uid = None
        self.session.close()
        logger.info("JSON-RPC connection closed")

    # Convenience methods (same as XmlRpcClient)
    def search(
        self,
        model: str,
        domain: Optional[List] = None,
        limit: int = 0
    ) -> Union[List[int], Dict]:
        """Search for records."""
        if domain is None:
            domain = []
        return self.execute_kw(model, "search", [domain], {"limit": limit})

    def search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        limit: int = 100
    ) -> Union[List[Dict], Dict]:
        """Search and read records."""
        if domain is None:
            domain = []
        kwargs = {"limit": limit}
        if fields:
            kwargs["fields"] = fields
        return self.execute_kw(model, "search_read", [domain], kwargs)

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None
    ) -> Union[List[Dict], Dict]:
        """Read records by IDs."""
        kwargs = {}
        if fields:
            kwargs["fields"] = fields
        return self.execute_kw(model, "read", [ids], kwargs)

    def create(
        self,
        model: str,
        values: Dict
    ) -> Union[int, Dict]:
        """Create a new record."""
        return self.execute_kw(model, "create", [values], {})

    def write(
        self,
        model: str,
        ids: List[int],
        values: Dict
    ) -> Union[bool, Dict]:
        """Update records."""
        return self.execute_kw(model, "write", [ids, values], {})

    def unlink(
        self,
        model: str,
        ids: List[int]
    ) -> Union[bool, Dict]:
        """Delete records."""
        return self.execute_kw(model, "unlink", [ids], {})

    def fields_get(
        self,
        model: str,
        attributes: Optional[List[str]] = None
    ) -> Union[Dict, Dict]:
        """Get field definitions for a model."""
        if attributes is None:
            attributes = ["string", "type", "help", "readonly", "required", "relation", "selection"]
        return self.execute_kw(model, "fields_get", [], {"attributes": attributes})


def create_client(config: OdooConfig) -> BaseClient:
    """
    Factory function to create the appropriate RPC client based on protocol.

    Args:
        config: Odoo configuration.

    Returns:
        XmlRpcClient or JsonRpc20Client instance.
    """
    if config.protocol == "json-rpc-2.0":
        logger.info("Creating JSON-RPC 2.0 client")
        return JsonRpc20Client(config)
    else:
        logger.info("Creating XML-RPC client")
        return XmlRpcClient(config)

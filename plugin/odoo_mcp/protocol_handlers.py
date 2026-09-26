"""
Odoo Protocol Handlers Module

Provides protocol abstraction layer for Odoo RPC communication:
- BaseClient: Abstract base class for RPC clients
- XmlRpcClient: XML-RPC client for Odoo 17-18
- JsonRpc20Client: legacy /jsonrpc client for Odoo 19/20 (deprecated upstream, removal in 22)
- Json2Client: External JSON-2 API client (/json/2, bearer API key) for Odoo 19+

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


class Json2Client(BaseClient):
    """External JSON-2 API client for Odoo 19+ (``POST /json/2/<model>/<method>``).

    Authenticates with a bearer API key (scope ``rpc``) instead of a password, so it
    works on Community without Odoo's Enterprise-only ``ai_mcp`` module. JSON-2 takes
    named arguments only: ``ids`` for the recordset plus the method's own parameters.
    """

    # Positional-argument names for the ORM methods the kit calls through
    # execute_kw(). Record methods take the ids as their first positional arg.
    MODEL_METHOD_ARGS = {
        "search": ("domain",),
        "search_read": ("domain", "fields"),
        "search_count": ("domain",),
        "fields_get": ("allfields", "attributes"),
        "create": ("vals_list",),
        "name_search": ("name",),
    }
    RECORD_METHOD_ARGS = {
        "read": ("fields",),
        "write": ("vals",),
        "unlink": (),
        "copy": ("default",),
    }

    def __init__(self, config: OdooConfig):
        """Initialize JSON-2 client."""
        super().__init__(config)
        self.session = requests.Session()
        self.session.headers.update(self._headers())

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"bearer {self.config.api_key}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "odoo-agent-pro-kit-mcp",
        }
        if self.config.database:
            headers["X-Odoo-Database"] = self.config.database
        return headers

    def _call(self, model: str, method: str, params: Dict) -> Any:
        """POST one JSON-2 call; return the result or ``{"error": message}``."""
        try:
            response = self.session.post(
                f"{self.config.get_base_url()}/json/2/{model}/{method}",
                json=params,
                timeout=self.config.request_timeout,
            )
        except requests.RequestException as e:
            logger.error(f"JSON-2 request error: {e}")
            return {"error": str(e)}

        try:
            body = response.json()
        except ValueError:
            body = None
        if response.status_code != 200:
            message = body.get("message") if isinstance(body, dict) else None
            message = message or f"HTTP {response.status_code}: {response.text[:200]}"
            logger.error(f"JSON-2 {model}.{method} failed: {message}")
            return {"error": message}
        return body

    def authenticate(self) -> Optional[int]:
        """Validate the API key and resolve its user id via ``res.users.context_get``."""
        if not self.config.api_key:
            logger.error("JSON-2 needs an API key (ODOO<version>_API_KEY)")
            return None
        result = self._call("res.users", "context_get", {})
        if isinstance(result, dict) and result.get("uid") and "error" not in result:
            self.uid = int(result["uid"])
            self._authenticated = True
            logger.info(f"JSON-2 authenticated successfully (UID: {self.uid})")
            return self.uid
        logger.error(f"JSON-2 authentication failed: {result}")
        return None

    def _named_params(self, method: str, args: List, kwargs: Dict) -> Dict[str, Any]:
        """Map execute_kw positional args to JSON-2 named args; ValueError if ambiguous."""
        params: Dict[str, Any] = {}
        if method in self.RECORD_METHOD_ARGS:
            names = self.RECORD_METHOD_ARGS[method]
            if args:
                params["ids"], args = args[0], args[1:]
        elif method in self.MODEL_METHOD_ARGS:
            names = self.MODEL_METHOD_ARGS[method]
        elif len(args) == 1 and isinstance(args[0], list) and all(isinstance(i, int) for i in args[0]):
            # execute_kw(model, "action_x", [[ids]]): legacy record-method call shape.
            names, params["ids"], args = (), args[0], []
        elif args:
            raise ValueError(f"JSON-2 needs keyword arguments for {method!r}; pass them in kwargs")
        else:
            names = ()
        if len(args) > len(names):
            raise ValueError(f"too many positional arguments for {method!r}; pass them in kwargs")
        params.update(zip(names, args))
        params.update(kwargs)
        if method == "create" and isinstance(params.get("vals_list"), dict):
            params["vals_list"] = [params["vals_list"]]
        return params

    def execute_kw(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """Execute a model method, mapping execute_kw-style args to JSON-2 named args."""
        if not self._authenticated:
            if not self.authenticate():
                return {"error": "Authentication failed"}
        try:
            params = self._named_params(method, list(args or []), dict(kwargs or {}))
        except ValueError as e:
            return {"error": str(e)}
        return self._call(model, method, params)

    def close(self) -> None:
        """Close JSON-2 session."""
        self._authenticated = False
        self.uid = None
        self.session.close()
        logger.info("JSON-2 connection closed")

    def search(self, model: str, domain: Optional[List] = None, limit: int = 0) -> Union[List[int], Dict]:
        """Search for records."""
        return self.execute_kw(model, "search", [domain or []], {"limit": limit} if limit else {})

    def search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        limit: int = 100
    ) -> Union[List[Dict], Dict]:
        """Search and read records."""
        kwargs: Dict[str, Any] = {"domain": domain or []}
        if fields:
            kwargs["fields"] = fields
        if limit:
            kwargs["limit"] = limit
        return self.execute_kw(model, "search_read", [], kwargs)

    def read(self, model: str, ids: List[int], fields: Optional[List[str]] = None) -> Union[List[Dict], Dict]:
        """Read records by IDs."""
        return self.execute_kw(model, "read", [ids], {"fields": fields} if fields else {})

    def create(self, model: str, values: Dict) -> Union[int, Dict]:
        """Create a new record and return its id (JSON-2 returns the created ids)."""
        result = self.execute_kw(model, "create", [[values]])
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        return result

    def write(self, model: str, ids: List[int], values: Dict) -> Union[bool, Dict]:
        """Update records."""
        return self.execute_kw(model, "write", [ids, values])

    def unlink(self, model: str, ids: List[int]) -> Union[bool, Dict]:
        """Delete records."""
        return self.execute_kw(model, "unlink", [ids])

    def fields_get(self, model: str, attributes: Optional[List[str]] = None) -> Union[Dict, Dict]:
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
        XmlRpcClient, JsonRpc20Client or Json2Client instance.
    """
    if config.protocol == "json-2":
        logger.info("Creating JSON-2 (API key) client")
        return Json2Client(config)
    if config.protocol == "json-rpc-2.0":
        logger.info("Creating JSON-RPC 2.0 client")
        return JsonRpc20Client(config)
    else:
        logger.info("Creating XML-RPC client")
        return XmlRpcClient(config)

"""
Odoo Connection Manager Module

Provides connection pooling and retry logic for Odoo RPC clients.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from queue import Queue, Empty
from dataclasses import dataclass
from threading import Lock

from .config import OdooConfig
from .protocol_handlers import BaseClient, XmlRpcClient, JsonRpc20Client, create_client

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Represents a connection in the pool."""
    client: BaseClient
    created_at: float
    last_used: float
    in_use: bool = False


class ConnectionPool:
    """Thread-safe connection pool for Odoo RPC clients."""

    def __init__(
        self,
        config: OdooConfig,
        pool_size: int = 10,
        max_idle_time: float = 300.0
    ):
        """
        Initialize connection pool.

        Args:
            config: Odoo configuration.
            pool_size: Maximum number of connections in pool.
            max_idle_time: Maximum idle time before connection is closed.
        """
        self.config = config
        self.pool_size = pool_size
        self.max_idle_time = max_idle_time
        self.connections: Queue = Queue(maxsize=pool_size)
        self.lock = Lock()
        self._closed = False

    def _create_connection(self) -> Optional[Connection]:
        """Create a new connection."""
        try:
            client = create_client(self.config)
            uid = client.authenticate()
            if uid:
                return Connection(
                    client=client,
                    created_at=time.time(),
                    last_used=time.time()
                )
            return None
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None

    def get_connection(self, timeout: float = 30.0) -> Optional[BaseClient]:
        """
        Get a connection from the pool.

        Args:
            timeout: Maximum time to wait for connection.

        Returns:
            Authenticated RPC client or None.
        """
        if self._closed:
            return None

        # Try to get from pool
        try:
            conn = self.connections.get(timeout=timeout)
            # Check if connection is still valid
            if time.time() - conn.last_used > self.max_idle_time:
                conn.client.close()
                conn = self._create_connection()
                if conn is None:
                    return None
            conn.in_use = True
            return conn.client
        except Empty:
            # Pool empty, create new if possible
            with self.lock:
                if self.connections.qsize() < self.pool_size:
                    conn = self._create_connection()
                    if conn:
                        conn.in_use = True
                        return conn.client
            return None

    def return_connection(self, client: BaseClient) -> None:
        """
        Return a connection to the pool.

        Args:
            client: The client to return.
        """
        if self._closed:
            client.close()
            return

        # Create a wrapper connection for the pool
        conn = Connection(
            client=client,
            created_at=time.time(),
            last_used=time.time()
        )
        try:
            self.connections.put_nowait(conn)
        except:
            # Pool full, close connection
            client.close()

    def close_all(self) -> None:
        """Close all connections in the pool."""
        self._closed = True
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.client.close()
            except Empty:
                break
        logger.info("Connection pool closed")

    def health_check(self) -> bool:
        """
        Check if pool has healthy connections.

        Returns:
            True if pool has at least one healthy connection.
        """
        try:
            conn = self.connections.get_nowait()
            if conn.client.is_authenticated:
                self.connections.put_nowait(conn)
                return True
            # Try to reconnect
            if conn.client.authenticate():
                self.connections.put_nowait(conn)
                return True
            return False
        except Empty:
            return False


class ConnectionManager:
    """Manages Odoo connections with retry logic and health checks."""

    def __init__(self, config: OdooConfig):
        """
        Initialize connection manager.

        Args:
            config: Odoo configuration.
        """
        self.config = config
        self.retry_attempts = config.retry_attempts
        self.retry_delays = [1.0, 2.0, 4.0]  # Exponential backoff
        self.pool: Optional[ConnectionPool] = None

    def _create_pool(self) -> ConnectionPool:
        """Create a new connection pool."""
        return ConnectionPool(
            config=self.config,
            pool_size=self.config.connection_pool_size,
            max_idle_time=self.config.cache_ttl
        )

    def initialize(self) -> bool:
        """
        Initialize the connection manager.

        Returns:
            True if initialization successful.
        """
        try:
            self.pool = self._create_pool()
            # Test connection
            client = self.get_connection()
            if client:
                self.return_connection(client)
                logger.info("Connection manager initialized successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to initialize connection manager: {e}")
            return False

    def get_connection(self, timeout: float = 30.0) -> Optional[BaseClient]:
        """
        Get a connection with retry logic.

        Args:
            timeout: Maximum time to wait for connection.

        Returns:
            Authenticated RPC client or None.
        """
        if not self.pool:
            self.pool = self._create_pool()

        for attempt in range(self.retry_attempts):
            try:
                client = self.pool.get_connection(timeout=timeout)
                if client and client.is_authenticated:
                    return client

                # Try to authenticate
                if client:
                    if client.authenticate():
                        return client
                    self.pool.return_connection(client)

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")

            # Wait before retry
            if attempt < self.retry_attempts - 1:
                delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

        logger.error("Failed to get connection after all retry attempts")
        return None

    def return_connection(self, client: BaseClient) -> None:
        """
        Return a connection to the pool.

        Args:
            client: The client to return.
        """
        if self.pool:
            self.pool.return_connection(client)

    def close_connection(self, client: BaseClient) -> None:
        """
        Close a specific connection.

        Args:
            client: The client to close.
        """
        client.close()
        self.return_connection(client)

    def close_all(self) -> None:
        """Close all connections."""
        if self.pool:
            self.pool.close_all()
        logger.info("All connections closed")

    def health_check(self) -> bool:
        """
        Check connection health.

        Returns:
            True if connections are healthy.
        """
        if not self.pool:
            return False
        return self.pool.health_check()

    def execute_with_retry(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Execute a method with automatic retry on failure.

        Args:
            model: Odoo model name
            method: Method name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Method result or error.
        """
        for attempt in range(self.retry_attempts):
            client = self.get_connection()
            if not client:
                return {"error": "Failed to get connection"}

            try:
                result = client.execute_kw(model, method, args, kwargs)

                # Check for error in result
                if isinstance(result, dict) and "error" in result:
                    error = result["error"]
                    # Retry on transient errors
                    if self._is_retryable_error(error):
                        logger.warning(f"Retryable error: {error}")
                        if attempt < self.retry_attempts - 1:
                            delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                            time.sleep(delay)
                            continue
                    return result

                # Success
                self.return_connection(client)
                return result

            except Exception as e:
                logger.error(f"Execute error: {e}")
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    time.sleep(delay)
                    continue
                return {"error": str(e)}
            finally:
                # Always return connection
                self.return_connection(client)

        return {"error": "Max retries exceeded"}

    @staticmethod
    def _is_retryable_error(error: Any) -> bool:
        """Check if error is retryable."""
        if isinstance(error, str):
            retryable_keywords = [
                "connection",
                "timeout",
                "network",
                "temporary",
                "refused"
            ]
            return any(kw.lower() in error.lower() for kw in retryable_keywords)
        return False


def create_connection_manager(config: OdooConfig) -> ConnectionManager:
    """
    Factory function to create a connection manager.

    Args:
        config: Odoo configuration.

    Returns:
        ConnectionManager instance.
    """
    return ConnectionManager(config)

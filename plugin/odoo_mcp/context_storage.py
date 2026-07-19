"""
Odoo Context Storage Module

Manages atomic writes to version-specific directories.
"""

import json
import logging
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .config import OdooConfig
from .model_extractor import ModelContext

logger = logging.getLogger(__name__)


@dataclass
class ContextMetadata:
    """Metadata about stored context."""
    version: str
    protocol: str
    database: str
    created_at: str
    checksum: str
    model_count: int
    file_path: str


class ContextStorage:
    """Manages storage of Odoo model contexts."""

    # Base directory for context storage (plugin/skills root)
    BASE_DIR = Path(__file__).resolve().parent.parent / "skills"

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize context storage.

        Args:
            base_dir: Base directory for storing contexts.
        """
        self.base_dir = base_dir or self.BASE_DIR

    def get_version_dir(self, version: str) -> Path:
        """
        Get version-specific directory.

        Args:
            version: Odoo version (e.g., "17.0", "18.0", "19.0").

        Returns:
            Path to version directory.
        """
        # Extract major version (e.g., "18.0" -> "18")
        major_version = version.split('.')[0]
        return self.base_dir / f"Odoo{major_version}ExistingDependencyContext"

    def get_context_file(self, version: str) -> Path:
        """
        Get path to context JSON file.

        Args:
            version: Odoo version.

        Returns:
            Path to context file.
        """
        return self.get_version_dir(version) / "context.json"

    def save_context(
        self,
        version: str,
        contexts: Dict[str, ModelContext],
        config: OdooConfig,
        checksum: str
    ) -> ContextMetadata:
        """
        Save contexts to version-specific directory.

        Args:
            version: Odoo version.
            contexts: Dict of model contexts.
            config: Odoo configuration.
            checksum: Checksum of the data.

        Returns:
            ContextMetadata about saved context.
        """
        version_dir = self.get_version_dir(version)
        version_dir.mkdir(parents=True, exist_ok=True)

        # Serialize contexts
        from .context_serializer import ContextSerializer
        serializer = ContextSerializer(config)

        data = serializer.serialize_contexts(contexts)
        data["metadata"] = {
            "version": version,
            "protocol": config.protocol,
            "database": config.database,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "checksum": checksum,
            "model_count": len(contexts)
        }

        # Atomic write: temp file then rename
        context_file = self.get_context_file(version)
        temp_file = context_file.with_suffix(".tmp")

        try:
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            # Atomic rename
            temp_file.replace(context_file)

            logger.info(f"Saved context for {version} to {context_file}")

            return ContextMetadata(
                version=version,
                protocol=config.protocol or "unknown",
                database=config.database,
                created_at=data["metadata"]["created_at"],
                checksum=checksum,
                model_count=len(contexts),
                file_path=str(context_file)
            )

        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            logger.error(f"Failed to save context: {e}")
            raise

    def load_context(self, version: str) -> Optional[Dict[str, Any]]:
        """
        Load context from version-specific directory.

        Args:
            version: Odoo version.

        Returns:
            Context data dict or None if not found.
        """
        context_file = self.get_context_file(version)

        if not context_file.exists():
            logger.warning(f"Context file not found: {context_file}")
            return None

        try:
            with open(context_file, "r") as f:
                data = json.load(f)
            logger.info(f"Loaded context for {version} from {context_file}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse context file: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            return None

    def get_metadata(self, version: str) -> Optional[ContextMetadata]:
        """
        Get metadata for stored context.

        Args:
            version: Odoo version.

        Returns:
            ContextMetadata or None if not found.
        """
        data = self.load_context(version)
        if not data or "metadata" not in data:
            return None

        meta = data["metadata"]
        return ContextMetadata(
            version=meta.get("version", version),
            protocol=meta.get("protocol", "unknown"),
            database=meta.get("database", ""),
            created_at=meta.get("created_at", ""),
            checksum=meta.get("checksum", ""),
            model_count=meta.get("model_count", 0),
            file_path=str(self.get_context_file(version))
        )

    def delete_context(self, version: str) -> bool:
        """
        Delete stored context for a version.

        Args:
            version: Odoo version.

        Returns:
            True if deleted successfully.
        """
        version_dir = self.get_version_dir(version)

        if not version_dir.exists():
            return False

        try:
            shutil.rmtree(version_dir)
            logger.info(f"Deleted context for {version}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete context: {e}")
            return False

    def list_versions(self) -> List[str]:
        """
        List all stored context versions.

        Returns:
            List of version strings.
        """
        versions = []

        if not self.base_dir.exists():
            return versions

        for item in self.base_dir.iterdir():
            if item.is_dir() and "Odoo" in item.name and "ExistingDependencyContext" in item.name:
                # Extract version from directory name
                # e.g., "Odoo170ExistingDependencyContext" -> "17.0"
                # e.g., "Odoo180ExistingDependencyContext" -> "18.0"
                # e.g., "Odoo190ExistingDependencyContext" -> "19.0"
                name = item.name
                if name.startswith("Odoo") and "ExistingDependencyContext" in name:
                    version_num = name.replace("Odoo", "").replace("ExistingDependencyContext", "")
                    if version_num.isdigit() and len(version_num) >= 2:
                        # e.g., "18" -> "18.0"
                        version = f"{version_num}.0"
                        versions.append(version)

        return sorted(versions)

    def exists(self, version: str) -> bool:
        """
        Check if context exists for a version.

        Args:
            version: Odoo version.

        Returns:
            True if context exists.
        """
        return self.get_context_file(version).exists()

    def get_age(self, version: str) -> Optional[float]:
        """
        Get age of stored context in seconds.

        Args:
            version: Odoo version.

        Returns:
            Age in seconds or None if not found.
        """
        metadata = self.get_metadata(version)
        if not metadata:
            return None

        try:
            created = datetime.fromisoformat(metadata.created_at.replace("Z", "+00:00"))
            age = (datetime.utcnow() - created.replace(tzinfo=None)).total_seconds()
            return age
        except Exception:
            return None

    def is_stale(self, version: str, max_age: int = 3600) -> bool:
        """
        Check if context is stale.

        Args:
            version: Odoo version.
            max_age: Maximum age in seconds (default: 1 hour).

        Returns:
            True if context is stale or doesn't exist.
        """
        age = self.get_age(version)
        if age is None:
            return True
        return age > max_age


# Singleton instance
_storage: Optional[ContextStorage] = None


def get_storage() -> ContextStorage:
    """Get singleton storage instance."""
    global _storage
    if _storage is None:
        _storage = ContextStorage()
    return _storage

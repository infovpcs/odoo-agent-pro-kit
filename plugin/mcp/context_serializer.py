"""
Odoo Context Serializer Module

Serializes model contexts to JSON format with index generation.
"""

import json
import hashlib
import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from .model_extractor import (
    ModelInfo, FieldInfo, RelationshipInfo, ModelContext
)
from .config import OdooConfig

logger = logging.getLogger(__name__)


class ContextSerializer:
    """Serializes Odoo model contexts to JSON."""

    def __init__(self, config: OdooConfig):
        """
        Initialize context serializer.

        Args:
            config: Odoo configuration.
        """
        self.config = config
        self.version = config.odoo_version or "unknown"

    def serialize_model(self, context: ModelContext) -> Dict[str, Any]:
        """
        Serialize a single model context to JSON.

        Args:
            context: ModelContext to serialize.

        Returns:
            Dictionary representation.
        """
        return {
            "model": {
                "id": context.model.id,
                "name": context.model.name,
                "model": context.model.model,
                "is_transient": context.model.is_transient,
                "module": context.model.module,
                "state": context.model.state,
                "description": context.model.description
            },
            "fields": [
                {
                    "name": f.name,
                    "type": f.field_type,
                    "string": f.string,
                    "help": f.help,
                    "required": f.required,
                    "readonly": f.readonly,
                    "index": f.index,
                    "translate": f.translate,
                    "relation": f.relation,
                    "relation_field": f.relation_field,
                    "selection": f.selection,
                    "default": f.default,
                    "compute": f.compute,
                    "store": f.store,
                    "domain": f.domain,
                    "onchange": f.onchange
                }
                for f in context.fields
            ],
            "relationships": [
                {
                    "name": r.name,
                    "type": r.type,
                    "model": r.model,
                    "relation": r.relation,
                    "inverse_name": r.inverse_name
                }
                for r in context.relationships
            ]
        }

    def serialize_contexts(
        self,
        contexts: Dict[str, ModelContext]
    ) -> Dict[str, Any]:
        """
        Serialize multiple model contexts.

        Args:
            contexts: Dict of model_name -> ModelContext.

        Returns:
            Complete serialized context.
        """
        models = {}
        for model_name, context in contexts.items():
            models[model_name] = self.serialize_model(context)

        return {
            "version": self.version,
            "protocol": self.config.protocol,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "database": self.config.database,
            "model_count": len(models),
            "models": models
        }

    def serialize_to_json(
        self,
        contexts: Dict[str, ModelContext],
        pretty: bool = True
    ) -> str:
        """
        Serialize contexts to JSON string.

        Args:
            contexts: Dict of model contexts.
            pretty: Use pretty printing.

        Returns:
            JSON string.
        """
        data = self.serialize_contexts(contexts)

        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    def create_index(self, contexts: Dict[str, ModelContext]) -> Dict[str, Any]:
        """
        Create an index for fast lookups.

        Args:
            contexts: Dict of model contexts.

        Returns:
            Index data structure.
        """
        index = {
            "by_name": {},
            "by_model": {},
            "by_module": {},
            "relationships": {}
        }

        for model_name, context in contexts.items():
            # Index by display name
            name = context.model.name.lower()
            if name not in index["by_name"]:
                index["by_name"][name] = []
            index["by_name"][name].append(model_name)

            # Index by model
            index["by_model"][model_name] = {
                "name": context.model.name,
                "module": context.model.module,
                "is_transient": context.model.is_transient,
                "field_count": len(context.fields),
                "relationship_count": len(context.relationships)
            }

            # Index by module
            module = context.model.module or "unknown"
            if module not in index["by_module"]:
                index["by_module"][module] = []
            index["by_module"][module].append(model_name)

            # Build relationship graph
            for rel in context.relationships:
                if rel.relation not in index["relationships"]:
                    index["relationships"][rel.relation] = []
                index["relationships"][rel.relation].append({
                    "source": model_name,
                    "field": rel.name,
                    "type": rel.type
                })

        return index

    def compute_checksum(self, json_str: str) -> str:
        """
        Compute SHA256 checksum of JSON.

        Args:
            json_str: JSON string.

        Returns:
            Hex digest of checksum.
        """
        return hashlib.sha256(json_str.encode()).hexdigest()

    def validate_json(self, json_str: str) -> bool:
        """
        Validate JSON string.

        Args:
            json_str: JSON string to validate.

        Returns:
            True if valid.
        """
        try:
            json.loads(json_str)
            return True
        except json.JSONDecodeError:
            return False

    def deserialize_model(self, data: Dict[str, Any]) -> Optional[ModelContext]:
        """
        Deserialize a model context from JSON.

        Args:
            data: Dictionary representation.

        Returns:
            ModelContext or None if invalid.
        """
        try:
            model_data = data.get("model", {})
            model_info = ModelInfo(
                id=model_data.get("id"),
                name=model_data.get("name", ""),
                model=model_data.get("model", ""),
                is_transient=model_data.get("is_transient", False),
                module=model_data.get("module"),
                state=model_data.get("state"),
                description=model_data.get("description")
            )

            fields = []
            for f in data.get("fields", []):
                fields.append(FieldInfo(
                    name=f.get("name", ""),
                    field_type=f.get("type", "char"),
                    string=f.get("string", ""),
                    help=f.get("help"),
                    required=f.get("required", False),
                    readonly=f.get("readonly", False),
                    index=f.get("index", False),
                    translate=f.get("translate", False),
                    relation=f.get("relation"),
                    relation_field=f.get("relation_field"),
                    selection=f.get("selection"),
                    default=f.get("default"),
                    compute=f.get("compute"),
                    store=f.get("store", True),
                    domain=f.get("domain"),
                    onchange=f.get("onchange")
                ))

            relationships = []
            for r in data.get("relationships", []):
                relationships.append(RelationshipInfo(
                    name=r.get("name", ""),
                    type=r.get("type", ""),
                    model=r.get("model", ""),
                    relation=r.get("relation", ""),
                    inverse_name=r.get("inverse_name")
                ))

            return ModelContext(
                model=model_info,
                fields=fields,
                relationships=relationships
            )

        except Exception as e:
            logger.error(f"Failed to deserialize model: {e}")
            return None


def serialize_contexts_to_file(
    contexts: Dict[str, ModelContext],
    config: OdooConfig,
    output_path: Path,
    create_index: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to serialize contexts to file.

    Args:
        contexts: Dict of model contexts.
        config: Odoo configuration.
        output_path: Path to output file.
        create_index: Whether to create index file.

    Returns:
        Metadata about the serialization.
    """
    serializer = ContextSerializer(config)

    # Serialize
    json_str = serializer.serialize_to_json(contexts, pretty=True)

    # Write main file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json_str)

    # Compute checksum
    checksum = serializer.compute_checksum(json_str)

    # Create index if requested
    index_data = None
    if create_index:
        index = serializer.create_index(contexts)
        index_path = output_path.with_suffix(".index.json")
        index_path.write_text(json.dumps(index, indent=2))
        index_data = str(index_path)

    logger.info(f"Serialized {len(contexts)} models to {output_path}")

    return {
        "output_file": str(output_path),
        "index_file": index_data,
        "checksum": checksum,
        "model_count": len(contexts),
        "version": config.odoo_version,
        "protocol": config.protocol
    }

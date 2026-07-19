"""
Odoo Model Extractor Module

Provides model discovery and field extraction from Odoo databases.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .config import OdooConfig
from .protocol_handlers import BaseClient

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about an Odoo model."""
    id: int
    name: str  # Display name
    model: str  # Technical name
    is_transient: bool
    is_module: bool = False
    module: Optional[str] = None
    state: Optional[str] = None
    description: Optional[str] = None


@dataclass
class FieldInfo:
    """Information about a model field."""
    name: str
    field_type: str
    string: str
    help: Optional[str] = None
    required: bool = False
    readonly: bool = False
    index: bool = False
    translate: bool = False
    relation: Optional[str] = None
    relation_field: Optional[str] = None
    selection: Optional[List] = None
    default: Any = None
    compute: Optional[str] = None
    store: bool = True
    domain: Optional[str] = None
    onchange: Optional[str] = None


@dataclass
class RelationshipInfo:
    """Information about a model relationship."""
    name: str
    type: str  # many2one, one2many, many2many
    model: str
    relation: str  # Related model
    inverse_name: Optional[str] = None  # For one2many


@dataclass
class ModelContext:
    """Complete context for an Odoo model."""
    model: ModelInfo
    fields: List[FieldInfo] = field(default_factory=list)
    relationships: List[RelationshipInfo] = field(default_factory=list)


class ModelExtractor:
    """Extracts models and fields from Odoo database."""

    def __init__(self, client: BaseClient):
        """
        Initialize model extractor.

        Args:
            client: Authenticated RPC client.
        """
        self.client = client

    def discover_models(
        self,
        include_transient: bool = True,
        module_filter: Optional[List[str]] = None
    ) -> List[ModelInfo]:
        """
        Discover all models from the database.

        Args:
            include_transient: Include transient models (temp records).
            module_filter: Filter by module names (not supported in all versions).

        Returns:
            List of ModelInfo objects.
        """
        logger.info("Discovering models from database...")

        # Query ir.model - use only universally available fields
        # Note: 'module', 'description' fields changed/removed in Odoo 17+
        domain = []
        if not include_transient:
            domain.append(("transient", "=", False))

        result = self.client.search_read(
            "ir.model",
            domain=domain,
            fields=[
                "id", "name", "model", "transient", "state", "modules", "info"
            ],
            limit=0  # Get all
        )

        if isinstance(result, dict) and "error" in result:
            logger.error(f"Failed to discover models: {result}")
            return []

        models = []
        for record in result:
            model_name = record.get("model", "")
            
            # Use the actual modules string (comma separated), fallback to derivation
            modules_str = record.get("modules")
            if modules_str:
                # Odoo often gives "account, spreadsheet_account", we want the first one
                derived_module = modules_str.split(",")[0].strip()
            else:
                derived_module = model_name.split(".")[0] if model_name else None

            # Filter by module if specified
            if module_filter and derived_module not in module_filter:
                continue

            models.append(ModelInfo(
                id=record.get("id"),
                name=record.get("name", ""),
                model=model_name,
                is_transient=record.get("transient", False),
                is_module=bool(derived_module),
                module=derived_module,
                state=record.get("state"),
                description=record.get("info")
            ))

        logger.info(f"Discovered {len(models)} models")
        return models

    def extract_fields(self, model_name: str) -> List[FieldInfo]:
        """
        Extract all fields for a model.

        Args:
            model_name: Technical model name (e.g., 'res.partner').

        Returns:
            List of FieldInfo objects.
        """
        logger.debug(f"Extracting fields for model: {model_name}")

        # Use fields_get to get all field definitions
        fields = self.client.fields_get(model_name)

        if isinstance(fields, dict) and "error" in fields:
            logger.error(f"Failed to extract fields for {model_name}: {fields}")
            return []

        field_list = []
        for field_name, field_data in fields.items():
            # Determine field type
            field_type = field_data.get("type", "char")

            # Handle relation fields
            relation = None
            relation_field = None
            if field_type in ("many2one", "one2many", "many2many"):
                relation = field_data.get("relation")
                if field_type == "one2many":
                    relation_field = field_data.get("inverse_name")

            # Handle selection fields
            selection = None
            if field_type == "selection":
                selection = field_data.get("selection")

            field_list.append(FieldInfo(
                name=field_name,
                field_type=field_type,
                string=field_data.get("string", ""),
                help=field_data.get("help"),
                required=field_data.get("required", False),
                readonly=field_data.get("readonly", False),
                index=field_data.get("index", False),
                translate=field_data.get("translate", False),
                relation=relation,
                relation_field=relation_field,
                selection=selection,
                default=field_data.get("default"),
                compute=field_data.get("compute"),
                store=field_data.get("store", True),
                domain=field_data.get("domain"),
                onchange=field_data.get("onchange")
            ))

        logger.debug(f"Extracted {len(field_list)} fields for {model_name}")
        return field_list

    def build_relationships(
        self,
        fields: List[FieldInfo]
    ) -> List[RelationshipInfo]:
        """
        Build relationship map from fields.

        Args:
            fields: List of FieldInfo objects.

        Returns:
            List of RelationshipInfo objects.
        """
        relationships = []

        for f in fields:
            if f.field_type == "many2one":
                relationships.append(RelationshipInfo(
                    name=f.name,
                    type="many2one",
                    model="",  # Will be set by caller
                    relation=f.relation,
                    inverse_name=f.relation_field
                ))
            elif f.field_type == "one2many":
                relationships.append(RelationshipInfo(
                    name=f.name,
                    type="one2many",
                    model="",  # Will be set by caller
                    relation=f.relation,
                    inverse_name=f.relation_field
                ))
            elif f.field_type == "many2many":
                relationships.append(RelationshipInfo(
                    name=f.name,
                    type="many2many",
                    model="",  # Will be set by caller
                    relation=f.relation
                ))

        return relationships

    def get_model_context(self, model_name: str) -> Optional[ModelContext]:
        """
        Get complete context for a model.

        Args:
            model_name: Technical model name.

        Returns:
            ModelContext or None if failed.
        """
        # Get model info - use only universal fields
        models = self.client.search_read(
            "ir.model",
            domain=[["model", "=", model_name]],
            fields=["id", "name", "model", "transient", "modules", "info"],
            limit=1
        )

        if not models or isinstance(models, dict):
            logger.error(f"Model not found: {model_name}")
            return None

        model_data = models[0]
        model_name_value = model_data.get("model", "")
        
        modules_str = model_data.get("modules")
        if modules_str:
            derived_module = modules_str.split(",")[0].strip()
        else:
            derived_module = model_name_value.split(".")[0] if model_name_value else None

        model_info = ModelInfo(
            id=model_data.get("id"),
            name=model_data.get("name", ""),
            model=model_name_value,
            is_transient=model_data.get("transient", False),
            module=derived_module,
            description=model_data.get("info")
        )

        # Get fields
        fields = self.extract_fields(model_name)

        # Get relationships
        relationships = self.build_relationships(fields)

        return ModelContext(
            model=model_info,
            fields=fields,
            relationships=relationships
        )

    def get_all_contexts(
        self,
        include_transient: bool = True,
        batch_size: int = 100
    ) -> Dict[str, ModelContext]:
        """
        Get context for all models.

        Args:
            include_transient: Include transient models.
            batch_size: Number of models to process per batch.

        Returns:
            Dict mapping model names to ModelContext.
        """
        models = self.discover_models(include_transient=include_transient)
        contexts = {}
        total = len(models)

        logger.info(f"Extracting context for {total} models...")

        for i, model in enumerate(models):
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total}")

            context = self.get_model_context(model.model)
            if context:
                contexts[model.model] = context

        logger.info(f"Extracted context for {len(contexts)} models")
        return contexts


class ModelDiscovery:
    """High-level model discovery with caching."""

    def __init__(self, client: BaseClient):
        """Initialize model discovery."""
        self.client = client
        self.extractor = ModelExtractor(client)
        self._cache: Dict[str, ModelContext] = {}
        self._models_cache: Optional[List[ModelInfo]] = None

    def get_model(self, model_name: str, use_cache: bool = True) -> Optional[ModelContext]:
        """
        Get model context with caching.

        Args:
            model_name: Technical model name.
            use_cache: Use cached result if available.

        Returns:
            ModelContext or None.
        """
        if use_cache and model_name in self._cache:
            return self._cache[model_name]

        context = self.extractor.get_model_context(model_name)
        if context:
            self._cache[model_name] = context

        return context

    def list_models(
        self,
        search: Optional[str] = None,
        include_transient: bool = True,
        use_cache: bool = True,
        limit: Optional[int] = None
    ) -> List[ModelInfo]:
        """
        List models with optional search filter.

        Args:
            search: Search term to filter models.
            include_transient: Include transient models.
            use_cache: Use cached list if available.
            limit: Maximum number of results to return.

        Returns:
            List of ModelInfo objects.
        """
        if use_cache and self._models_cache is not None:
            models = self._models_cache
        else:
            models = self.extractor.discover_models(include_transient=include_transient)
            self._models_cache = models

        if search:
            search_lower = search.lower()
            models = [
                m for m in models
                if search_lower in m.name.lower() or search_lower in m.model.lower()
            ]

        if limit is not None:
            models = models[:limit]

        return models

    def search_models(
        self,
        query: str,
        limit: int = 20
    ) -> List[ModelInfo]:
        """
        Search models by query string.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of matching ModelInfo objects.
        """
        models = self.list_models(search=query)
        return models[:limit]

    def clear_cache(self) -> None:
        """Clear all caches."""
        self._cache.clear()
        self._models_cache = None
        logger.info("Model discovery cache cleared")

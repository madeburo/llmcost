"""Data loader for LLM models and pricing information from YAML."""

from importlib import resources
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Model:
    """Represents an LLM model with pricing information."""
    provider_id: str
    provider_name: str
    model_id: str
    name: str
    input_per_million: float
    output_per_million: float
    context_window: int


def load_models() -> List[Model]:
    """Load all LLM models and their prices from prices.yaml."""
    try:
        with resources.open_text("llm_cost.data", "prices.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or 'providers' not in data:
            raise ValueError("Invalid prices.yaml: missing 'providers' key")

        models: List[Model] = []

        for provider_id, provider_data in data['providers'].items():
            if not isinstance(provider_data, dict):
                continue
            provider_name = provider_data.get('name', provider_id)
            provider_models = provider_data.get('models', {})
            if not isinstance(provider_models, dict):
                continue
            for model_id, model_data in provider_models.items():
                try:
                    if not isinstance(model_data, dict):
                        continue
                    models.append(Model(
                        provider_id=provider_id,
                        provider_name=provider_name,
                        model_id=model_id,
                        name=model_data.get('name', model_id),
                        input_per_million=float(model_data.get('input', 0)),
                        output_per_million=float(model_data.get('output', 0)),
                        context_window=int(model_data.get('context', 0)),
                    ))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing model {provider_id}/{model_id}: {e}")

        if not models:
            raise ValueError("No valid models found in prices.yaml")

        return models
    except FileNotFoundError:
        logger.error("prices.yaml not found in package data")
        raise
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in prices.yaml: {e}")


def find_model(query: str) -> Optional[Model]:
    """Find a model by ID."""
    models = load_models()
    query_lower = query.lower()
    for model in models:
        if model.model_id.lower() == query_lower:
            return model
    return None


def search_models(query: str) -> List[Model]:
    """Search for models by name or provider."""
    models = load_models()
    query_lower = query.lower()
    return [
        m for m in models
        if query_lower in m.name.lower()
        or query_lower in m.model_id.lower()
        or query_lower in m.provider_name.lower()
        or query_lower in m.provider_id.lower()
    ]


def get_providers() -> Dict[str, List[Model]]:
    """Get all models grouped by provider."""
    models = load_models()
    providers: Dict[str, List[Model]] = {}
    for model in models:
        providers.setdefault(model.provider_name, []).append(model)
    return providers

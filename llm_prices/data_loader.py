"""Data loader for LLM models and pricing information from YAML."""

from importlib import resources
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Model:
    """Represents an LLM model with pricing information.
    
    Attributes:
        provider_id: Unique identifier for the provider (e.g., 'openai')
        provider_name: Display name of the provider (e.g., 'OpenAI')
        model_id: Unique identifier for the model (e.g., 'gpt-4')
        name: Display name of the model (e.g., 'GPT-4')
        input_per_million: Price per 1M input tokens in USD
        output_per_million: Price per 1M output tokens in USD
        context_window: Maximum context length in tokens
    """
    provider_id: str
    provider_name: str
    model_id: str
    name: str
    input_per_million: float
    output_per_million: float
    context_window: int


def load_models() -> List[Model]:
    """Load all LLM models and their prices from prices.yaml.
    
    Reads the prices.yaml file and parses it into Model objects.
    Handles errors gracefully with detailed logging.
    
    Returns:
        List of Model objects with pricing information
        
    Raises:
        FileNotFoundError: If prices.yaml is not included in package data
        ValueError: If prices.yaml contains invalid data
    """
    try:
        with resources.open_text("llm_prices.data", "prices.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data or 'providers' not in data:
            logger.error("Invalid prices.yaml structure: 'providers' key not found")
            raise ValueError("Invalid prices.yaml: missing 'providers' key")
        
        models: List[Model] = []
        
        for provider_id, provider_data in data['providers'].items():
            if not isinstance(provider_data, dict):
                logger.warning(f"Skipping invalid provider: {provider_id}")
                continue
            
            provider_name = provider_data.get('name', provider_id)
            provider_models = provider_data.get('models', {})
            
            if not isinstance(provider_models, dict):
                logger.warning(f"Provider {provider_id} has no models")
                continue
            
            for model_id, model_data in provider_models.items():
                try:
                    if not isinstance(model_data, dict):
                        logger.warning(f"Skipping invalid model: {provider_id}/{model_id}")
                        continue
                    
                    model = Model(
                        provider_id=provider_id,
                        provider_name=provider_name,
                        model_id=model_id,
                        name=model_data.get('name', model_id),
                        input_per_million=float(model_data.get('input', 0)),
                        output_per_million=float(model_data.get('output', 0)),
                        context_window=int(model_data.get('context', 0))
                    )
                    models.append(model)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing model {provider_id}/{model_id}: {e}")
                    continue
        
        if not models:
            logger.error("No valid models found in prices.yaml")
            raise ValueError("No valid models found in prices.yaml")
        
        logger.debug(f"Loaded {len(models)} models from {len(data['providers'])} providers")
        return models
    except FileNotFoundError:
        logger.error("prices.yaml not found in package data")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing prices.yaml: {e}")
        raise ValueError(f"Invalid YAML in prices.yaml: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading models: {e}")
        raise


def find_model(query: str) -> Optional[Model]:
    """Find a model by ID.
    
    Args:
        query: Model ID to search for (e.g., 'gpt-4', 'claude-opus')
        
    Returns:
        Model object if found, None otherwise
    """
    try:
        models = load_models()
        query_lower = query.lower()
        
        for model in models:
            if model.model_id.lower() == query_lower:
                return model
        
        return None
    except Exception as e:
        logger.error(f"Error finding model: {e}")
        return None


def search_models(query: str) -> List[Model]:
    """Search for models by name or provider.
    
    Performs case-insensitive search across model names and provider names.
    
    Args:
        query: Search query (e.g., 'gpt', 'claude', 'openai')
        
    Returns:
        List of matching Model objects
    """
    try:
        models = load_models()
        query_lower = query.lower()
        
        results = []
        for model in models:
            if (query_lower in model.name.lower() or
                query_lower in model.model_id.lower() or
                query_lower in model.provider_name.lower() or
                query_lower in model.provider_id.lower()):
                results.append(model)
        
        return results
    except Exception as e:
        logger.error(f"Error searching models: {e}")
        return []


def get_providers() -> Dict[str, List[Model]]:
    """Get all models grouped by provider.
    
    Returns:
        Dictionary with provider names as keys and lists of models as values
    """
    try:
        models = load_models()
        providers: Dict[str, List[Model]] = {}
        
        for model in models:
            if model.provider_name not in providers:
                providers[model.provider_name] = []
            providers[model.provider_name].append(model)
        
        return providers
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        return {}

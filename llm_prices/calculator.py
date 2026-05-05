"""Calculator for token counts and LLM API costs."""

import logging
from typing import List
from dataclasses import dataclass

from llm_prices.data_loader import Model

logger = logging.getLogger(__name__)


@dataclass
class CalculationResult:
    """Result of a cost calculation for a model.
    
    Attributes:
        model: The Model object
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        input_cost: Cost for input tokens in USD
        output_cost: Cost for output tokens in USD
        total_cost: Total cost in USD
    """
    model: Model
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text.
    
    Uses tiktoken when available. Falls back to a simple word-count heuristic.
    Falls back to a basic calculation for rough estimation.
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated number of tokens
    """
    if not text:
        return 0
    
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(text))
        logger.debug(f"Estimated {token_count} tokens using tiktoken")
        return token_count
    except ImportError:
        words = text.split()
        estimated = max(1, len(words))  # At least 1 token
        logger.debug(f"Estimated {estimated} tokens using word count")
        return estimated
    except Exception as e:
        logger.warning(f"Error estimating tokens: {e}, falling back to word count")
        words = text.split()
        return max(1, len(words))


def calculate(model: Model, input_tokens: int, output_tokens: int) -> CalculationResult:
    """Calculate the cost for a single model.
    
    Computes input and output costs based on per-million-token pricing.
    
    Args:
        model: The Model to calculate cost for
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        CalculationResult with detailed cost breakdown
    """
    try:
        input_cost = (input_tokens / 1_000_000) * model.input_per_million
        output_cost = (output_tokens / 1_000_000) * model.output_per_million
        total_cost = input_cost + output_cost
        
        return CalculationResult(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost
        )
    except Exception as e:
        logger.error(f"Error calculating cost for {model.name}: {e}")
        raise


def calculate_all(models: List[Model], input_tokens: int, output_tokens: int) -> List[CalculationResult]:
    """Calculate costs for all models and sort by total cost.
    
    Args:
        models: List of models to calculate for
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        List of CalculationResult objects sorted by total_cost (ascending)
    """
    results = []
    
    for model in models:
        try:
            result = calculate(model, input_tokens, output_tokens)
            results.append(result)
        except Exception as e:
            logger.warning(f"Skipping {model.name}: {e}")
            continue
    
    # Sort by total cost, ascending (cheapest first)
    results.sort(key=lambda r: r.total_cost)
    
    return results


def format_cost(cost: float) -> str:
    """Format cost as a string with currency symbol.
    
    Args:
        cost: Cost in USD
        
    Returns:
        Formatted cost string (e.g., '$0.001234')
    """
    if cost < 0.000001:
        return "$0.000000"
    elif cost < 0.001:
        return f"${cost:.6f}"
    elif cost < 1:
        return f"${cost:.6f}"
    else:
        return f"${cost:.2f}"


def format_tokens(count: int) -> str:
    """Format token count as a string with thousands separators.
    
    Args:
        count: Number of tokens
        
    Returns:
        Formatted string (e.g., '10,000')
    """
    return f"{count:,}"

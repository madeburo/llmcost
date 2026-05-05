"""Calculator for token counts and LLM API costs."""

import logging
from typing import List
from dataclasses import dataclass

from llm_cost.data_loader import Model

logger = logging.getLogger(__name__)


@dataclass
class CalculationResult:
    """Result of a cost calculation for a model."""
    model: Model
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text."""
    if not text:
        return 0
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        return max(1, len(text.split()))
    except Exception as e:
        logger.warning(f"Error estimating tokens: {e}, falling back to word count")
        return max(1, len(text.split()))


def calculate(model: Model, input_tokens: int, output_tokens: int) -> CalculationResult:
    """Calculate the cost for a single model."""
    input_cost = (input_tokens / 1_000_000) * model.input_per_million
    output_cost = (output_tokens / 1_000_000) * model.output_per_million
    return CalculationResult(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=input_cost + output_cost,
    )


def calculate_all(models: List[Model], input_tokens: int, output_tokens: int) -> List[CalculationResult]:
    """Calculate costs for all models and sort by total cost."""
    results = []
    for model in models:
        try:
            results.append(calculate(model, input_tokens, output_tokens))
        except Exception as e:
            logger.warning(f"Skipping {model.name}: {e}")
    results.sort(key=lambda r: r.total_cost)
    return results


def format_cost(cost: float) -> str:
    """Format cost as a USD string."""
    if cost < 0.000001:
        return "$0.000000"
    elif cost < 1:
        return f"${cost:.6f}"
    else:
        return f"${cost:.2f}"


def format_tokens(count: int) -> str:
    """Format token count with thousands separators."""
    return f"{count:,}"

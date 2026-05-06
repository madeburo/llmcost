"""Display utilities for printing formatted tables and results."""

import logging
from typing import List

from rich.console import Console
from rich.table import Table

from llm_cost.data_loader import Model
from llm_cost.calculator import CalculationResult, format_cost, format_tokens

logger = logging.getLogger(__name__)

console = Console()


def format_price_per_million(price: float) -> str:
    return f"${price:.2f}"


def format_tier(tier: str) -> str:
    """Format efficiency tier with color."""
    tier_colors = {
        "flagship": "bright_magenta",
        "advanced": "bright_blue",
        "standard": "bright_green",
        "budget": "bright_yellow",
    }
    color = tier_colors.get(tier, "white")
    return f"[{color}]{tier}[/{color}]"


def print_models_table(models: List[Model], title: str = "LLM Models") -> None:
    if not models:
        console.print("[yellow]No models to display[/yellow]")
        return
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Provider", style="magenta", width=15)
    table.add_column("Model", style="green", width=25)
    table.add_column("Tier", style="white", width=12)
    table.add_column("Input $/1M", style="yellow", width=12)
    table.add_column("Output $/1M", style="yellow", width=12)
    table.add_column("Context", style="white", width=12)
    for idx, model in enumerate(models, 1):
        table.add_row(
            str(idx),
            model.provider_name,
            model.name,
            format_tier(model.efficiency_tier),
            format_price_per_million(model.input_per_million),
            format_price_per_million(model.output_per_million),
            format_tokens(model.context_window),
        )
    console.print(table)


def print_calc_table(results: List[CalculationResult], input_tokens: int, output_tokens: int, sort_by: str = "cost") -> None:
    if not results:
        console.print("[yellow]No results to display[/yellow]")
        return
    title = f"Cost estimate · {input_tokens} input + {output_tokens} output"
    if sort_by == "value":
        title += " · sorted by value"
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Provider", style="magenta", width=15)
    table.add_column("Model", style="green", width=22)
    table.add_column("Tier", style="white", width=12)
    table.add_column("Total cost", style="yellow", width=12)
    
    if sort_by == "value":
        table.add_column("Value", style="bright_green", width=10)
        table.add_column("vs best", style="white", width=12)
        best_value = results[0].value_score if results else 0
        for idx, result in enumerate(results, 1):
            ratio = best_value / result.value_score if result.value_score > 0 else 1
            vs_text = "[green]best[/green]" if ratio == 1.0 else f"[yellow]{ratio:.1f}x worse[/yellow]"
            value_display = f"{result.value_score:.0f}"
            table.add_row(
                str(idx), 
                result.model.provider_name, 
                result.model.name,
                format_tier(result.model.efficiency_tier),
                format_cost(result.total_cost), 
                value_display,
                vs_text
            )
    else:
        table.add_column("vs cheapest", style="white", width=15)
        cheapest_cost = results[0].total_cost if results else 0
        for idx, result in enumerate(results, 1):
            multiplier = result.total_cost / cheapest_cost if cheapest_cost > 0 else 1
            vs_text = "[green]cheapest[/green]" if multiplier == 1.0 else f"[yellow]{multiplier:.1f}x[/yellow]"
            table.add_row(
                str(idx), 
                result.model.provider_name, 
                result.model.name,
                format_tier(result.model.efficiency_tier),
                format_cost(result.total_cost), 
                vs_text
            )
    console.print(table)


def print_compare_table(results: List[CalculationResult], input_tokens: int, output_tokens: int) -> None:
    if not results:
        console.print("[yellow]No results to display[/yellow]")
        return
    title = f"Model Comparison · {input_tokens} input + {output_tokens} output"
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Provider", style="magenta", width=15)
    table.add_column("Model", style="green", width=22)
    table.add_column("Tier", style="white", width=12)
    table.add_column("Input Cost", style="blue", width=12)
    table.add_column("Output Cost", style="blue", width=12)
    table.add_column("Total Cost", style="yellow", width=12)
    table.add_column("Value", style="bright_green", width=10)
    table.add_column("Context", style="white", width=12)
    for result in results:
        table.add_row(
            result.model.provider_name,
            result.model.name,
            format_tier(result.model.efficiency_tier),
            format_cost(result.input_cost),
            format_cost(result.output_cost),
            format_cost(result.total_cost),
            f"{result.value_score:.0f}",
            format_tokens(result.model.context_window),
        )
    console.print(table)

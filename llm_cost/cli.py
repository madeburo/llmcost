"""Command-line interface for llmprices."""

from enum import Enum
from typing import List, Optional

import typer

from llm_cost import __version__
from llm_cost.calculator import calculate, calculate_all, estimate_tokens, format_cost
from llm_cost.data_loader import find_model, get_providers, load_models
from llm_cost.display import console, print_calc_table, print_compare_table, print_models_table


class SortField(str, Enum):
    input = "input"
    output = "output"
    context = "context"
    name = "name"


app = typer.Typer(
    name="llm-cost",
    help="Compare LLM API prices across providers.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"llm-cost [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v",
        callback=version_callback, is_eager=True, help="Show version.",
    ),
) -> None:
    """Run the llm-cost CLI."""


def _matches_provider(model, provider: str) -> bool:
    p = provider.lower()
    return model.provider_id.lower() == p or model.provider_name.lower() == p


def _matches_search(model, query: str) -> bool:
    q = query.lower()
    return (q in model.name.lower() or q in model.model_id.lower()
            or q in model.provider_name.lower() or q in model.provider_id.lower())


@app.command("list", help="List all available models and their prices.")
def cmd_list(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider."),
    sort: SortField = typer.Option(SortField.input, "--sort", "-s", help="Sort by: input | output | context | name"),
    search: Optional[str] = typer.Option(None, "--search", "-q", help="Search by model or provider name."),
) -> None:
    models = load_models()
    if provider:
        models = [m for m in models if _matches_provider(m, provider)]
        if not models:
            console.print(f"[red]No models found for provider:[/red] {provider}")
            raise typer.Exit(1)
    if search:
        models = [m for m in models if _matches_search(m, search)]
        if not models:
            console.print(f"[red]No models found for query:[/red] {search}")
            raise typer.Exit(1)
    if sort == SortField.output:
        models = sorted(models, key=lambda m: m.output_per_million)
    elif sort == SortField.context:
        models = sorted(models, key=lambda m: m.context_window, reverse=True)
    elif sort == SortField.name:
        models = sorted(models, key=lambda m: m.name.lower())
    else:
        models = sorted(models, key=lambda m: m.input_per_million)
    title = "LLM API Prices"
    if provider:
        title += f" - {provider}"
    if search:
        title += f" - search: {search}"
    print_models_table(models, title=title)
    console.print(f"[dim]  {len(models)} models  ·  sorted by {sort.value}[/dim]\n")


@app.command("calc", help="Calculate cost for a prompt.")
def cmd_calc(
    prompt: Optional[str] = typer.Argument(None, help="Prompt text to estimate cost for."),
    input_tokens: Optional[int] = typer.Option(None, "--input", "-i", min=0, help="Input token count."),
    output_tokens: int = typer.Option(500, "--output", "-o", min=0, help="Expected output token count."),
    top: int = typer.Option(10, "--top", "-n", min=1, help="Show top N cheapest models."),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Show only a specific model."),
) -> None:
    if prompt is None and input_tokens is None:
        console.print("[red]Provide a prompt or --input token count.[/red]")
        console.print("  Example: [cyan]llm-cost calc 'Hello, world!' --output 200[/cyan]")
        raise typer.Exit(1)
    if input_tokens is None:
        input_tokens = estimate_tokens(prompt or "")
        console.print(f"[dim]  Estimated input tokens: {input_tokens:,}[/dim]")
    if model:
        selected = find_model(model)
        if not selected:
            console.print(f"[red]Model not found:[/red] {model}")
            raise typer.Exit(1)
        print_calc_table([calculate(selected, input_tokens, output_tokens)], input_tokens, output_tokens)
        return
    models = load_models()
    if provider:
        models = [m for m in models if _matches_provider(m, provider)]
        if not models:
            console.print(f"[red]No models found for provider:[/red] {provider}")
            raise typer.Exit(1)
    results = calculate_all(models, input_tokens, output_tokens)[:top]
    if not results:
        console.print("[yellow]No results to display[/yellow]")
        raise typer.Exit(1)
    print_calc_table(results, input_tokens, output_tokens)
    cheapest = results[0]
    console.print(
        f"\n  [bold bright_green]Cheapest:[/bold bright_green] [bold]{cheapest.model.name}[/bold]"
        f" ({cheapest.model.provider_name}) - {format_cost(cheapest.total_cost)}\n"
    )


@app.command("compare", help="Compare specific models side by side.")
def cmd_compare(
    models: List[str] = typer.Argument(..., help="Model IDs to compare."),
    input_tokens: int = typer.Option(1000, "--input", "-i", min=0, help="Input token count."),
    output_tokens: int = typer.Option(500, "--output", "-o", min=0, help="Output token count."),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Estimate tokens from prompt text."),
) -> None:
    if len(models) < 2:
        console.print("[red]Provide at least 2 model IDs to compare.[/red]")
        console.print("  Example: [cyan]llm-cost compare gpt-5 o3 gemini-2-5-pro[/cyan]")
        raise typer.Exit(1)
    if prompt:
        input_tokens = estimate_tokens(prompt)
        console.print(f"[dim]  Estimated input tokens: {input_tokens:,}[/dim]")
    resolved = []
    for query in models:
        selected = find_model(query)
        if not selected:
            console.print(f"[red]Model not found:[/red] {query}")
            raise typer.Exit(1)
        resolved.append(selected)
    results = calculate_all(resolved, input_tokens, output_tokens)
    print_compare_table(results, input_tokens, output_tokens)


@app.command("providers", help="List all supported providers.")
def cmd_providers() -> None:
    providers = get_providers()
    if not providers:
        console.print("[yellow]No providers to display[/yellow]")
        raise typer.Exit(1)
    for provider_name, models in providers.items():
        model_names = ", ".join(m.name for m in models)
        console.print(f"  [bold]{provider_name}[/bold] [dim]({len(models)} models)[/dim]")
        console.print(f"    [dim]{model_names}[/dim]")
        console.print()


def run() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    run()

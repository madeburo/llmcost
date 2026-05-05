from typer.testing import CliRunner

from llm_cost.cli import app


runner = CliRunner()


def test_list_outputs_per_million_prices():
    result = runner.invoke(app, ["list", "--provider", "openai", "--sort", "input"])

    assert result.exit_code == 0
    assert "GPT-5.4 Nano" in result.output
    assert "$0.20" in result.output


def test_list_rejects_invalid_sort():
    result = runner.invoke(app, ["list", "--sort", "madeup"])

    assert result.exit_code != 0
    assert "madeup" in result.output


def test_calc_unknown_provider_exits_without_traceback():
    result = runner.invoke(app, ["calc", "--input", "1000", "--provider", "nope"])

    assert result.exit_code == 1
    assert "No models found for provider" in result.output
    assert "Traceback" not in result.output


def test_calc_valid_provider():
    result = runner.invoke(app, ["calc", "--input", "1000", "--output", "500", "--top", "1"])

    assert result.exit_code == 0
    assert "Cheapest" in result.output

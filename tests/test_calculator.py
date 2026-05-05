from llm_cost.calculator import calculate
from llm_cost.data_loader import Model


def test_calculate_costs_per_million_tokens():
    model = Model(
        provider_id="test",
        provider_name="Test",
        model_id="test-model",
        name="Test Model",
        input_per_million=1.0,
        output_per_million=2.0,
        context_window=1000,
    )

    result = calculate(model, input_tokens=1000, output_tokens=500)

    assert result.input_cost == 0.001
    assert result.output_cost == 0.001
    assert result.total_cost == 0.002
